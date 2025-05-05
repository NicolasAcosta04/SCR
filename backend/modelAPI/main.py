"""
News Classification and Recommendation API
Handles article classification, sentiment analysis, and personalized recommendations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from category_mappings import validate_category, validate_subcategory, map_to_main_category, map_to_subcategory, get_subcategories
from recommendation import RecommendationSystem, Article
from news_fetcher import NewsFetcher

# Initialize FastAPI application
app = FastAPI(title="News Classification API")

# Configure CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
recommendation_system = RecommendationSystem()
news_fetcher = NewsFetcher()

# Model configuration
repository_id = "nicolasacosta/roberta-base_bbc-news"

# Load model configuration
config = AutoConfig.from_pretrained(repository_id)

# Set device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the pre-trained model and tokenizer
model = AutoModelForSequenceClassification.from_pretrained(repository_id, config=config).to(device)
tokenizer = AutoTokenizer.from_pretrained(repository_id)

# Pydantic models for request/response validation
class TextRequest(BaseModel):
    """Model for text classification requests"""
    text: str
    category: Optional[str] = None

class ArticleRequest(BaseModel):
    """Model for article processing requests"""
    article_id: str
    title: str
    content: str

class ClassificationResponse(BaseModel):
    """Model for classification response"""
    category: str
    confidence: float

class ArticleResponse(BaseModel):
    """Model for article response with metadata"""
    article_id: str
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    confidence: float
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None
    image_url: Optional[str] = None

class FetchArticlesRequest(BaseModel):
    """Model for article fetching requests"""
    query: Optional[str] = None
    category: Optional[str] = None
    language: str = "en"
    page_size: int = 10
    days_back: int = 7
    page: int = 1

@app.post("/articles/fetch", response_model=List[ArticleResponse])
async def fetch_and_classify_articles(request: FetchArticlesRequest):
    """
    Fetch and classify articles from news sources
    Retrieves articles based on query parameters and classifies them using the ML model
    """
    # Fetch articles from news API with force_refresh=True to bypass cache
    articles = await news_fetcher.fetch_articles(
        query=request.query,
        category=request.category,
        language=request.language,
        page_size=request.page_size,
        days_back=request.days_back,
        page=request.page,
        force_refresh=True  # Always force refresh to get fresh articles
    )
    
    classified_articles = []
    for article in articles:
        # Combine title and content for better context, but limit the content length
        content = article['content']
        if len(content) > 400:  # Limit content length to ensure we stay within token limits
            content = content[:400] + "..."
            
        text = f"{article['title']} {content}"
        
        # Tokenize and prepare input for model
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
        
        # Perform classification
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, predicted_class = torch.max(predictions, dim=1)
            
            # Get the predicted label
            predicted_label = model.config.id2label[predicted_class.item()]
            confidence = confidence.item()
            
        # Validate category if provided
        if request.category:
            if not validate_category(predicted_label):
                raise HTTPException(status_code=400, detail="Invalid category")
            predicted_label = map_to_main_category(predicted_label)
        
        # Get subcategory based on article content analysis
        subcategory = map_to_subcategory(predicted_label, text)
        
        # Create article object and add to recommendation system
        article_obj = Article(
            article_id=article["article_id"],
            title=article["title"],
            content=article["content"],
            category=predicted_label,
            subcategory=subcategory,
            confidence=confidence,
            source=article["source"],
            url=article["url"],
            published_at=article["published_at"],
            image_url=article["image_url"]
        )
        
        recommendation_system.add_article(article_obj)        
            
        # Create response object
        classified_articles.append(ArticleResponse(
            article_id=article["article_id"],
            title=article["title"],
            content=article["content"],
            category=predicted_label.upper(),
            subcategory=subcategory,
            confidence=confidence,
            source=article["source"],
            url=article["url"],
            published_at=article["published_at"],
            image_url=article["image_url"]
        ))
    
    return classified_articles

@app.get("/articles/recommendations/{user_id}", response_model=List[ArticleResponse])
async def get_recommendations(user_id: str, num_recommendations: int = 5):
    """
    Get personalized article recommendations for a user
    Uses the recommendation system to generate tailored article suggestions
    """
    try:
        recommended_articles = recommendation_system.get_recommendations(user_id, num_recommendations)
        return [
            ArticleResponse(
                article_id=article.article_id,
                title=article.title,
                content=article.content,
                category=article.category,
                subcategory=article.subcategory,
                confidence=article.confidence,
                source=article.source,
                url=article.url,
                published_at=article.published_at,
                image_url=article.image_url
            )
            for article in recommended_articles
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/articles/update-preferences/{user_id}")
async def update_user_preferences(
    user_id: str,
    article_id: str,
    category: str,
    confidence: float
):
    """
    Update user preferences based on article interaction
    Used to improve recommendation accuracy over time
    """
    try:
        recommendation_system.update_user_preferences(user_id, category, confidence, article_id)
        return {"message": "User preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: TextRequest):
    """
    Classify a text into news categories
    Uses the ML model to predict the category of the input text
    """
    try:
        # Validate input category if provided
        if request.category:
            if not validate_category(request.category):
                raise HTTPException(status_code=400, detail="Invalid category")
            request.category = map_to_main_category(request.category)

        # Process the text
        inputs = tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
        
        # Perform classification
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, predicted_class = torch.max(predictions, dim=1)
            
            # Get the predicted label
            predicted_label = model.config.id2label[predicted_class.item()]
            print(f"\nClassification debug:")
            print(f"Input text: {request.text}")
            print(f"Raw predictions: {predictions}")
            print(f"Predicted class: {predicted_class.item()}")
            print(f"Predicted label: {predicted_label}")
            print(f"Confidence: {confidence.item()}")
            
            return ClassificationResponse(
                category=predicted_label.lower(),
                confidence=confidence.item()
            )
    except Exception as e:
        print(f"Classification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-sentiment")
async def analyze_sentiment(request: TextRequest):
    """
    Analyze the sentiment of a text
    Uses the ML model to determine if the text has positive or negative sentiment
    """
    try:
        inputs = tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, predicted_class = torch.max(predictions, dim=1)
            
            sentiment = "positive" if predicted_class.item() == 1 else "negative"
            return {
                "sentiment": sentiment,
                "confidence": confidence.item()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)