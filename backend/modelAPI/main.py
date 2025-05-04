from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, AutoConfig
from category_mappings import validate_category, validate_subcategory, map_to_main_category, map_to_subcategory, get_subcategories
from recommendation import RecommendationSystem, Article
from news_fetcher import NewsFetcher

app = FastAPI(title="News Classification API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
recommendation_system = RecommendationSystem()
news_fetcher = NewsFetcher()

# Load models and tokenizers
repository_id = "nicolasacosta/roberta-base_bbc-news"

# Load model config
config = AutoConfig.from_pretrained(repository_id)
# print(f"\nOriginal max position embeddings: {config.max_position_embeddings}")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the model and tokenizer
model = AutoModelForSequenceClassification.from_pretrained(repository_id, config=config).to(device)
tokenizer = AutoTokenizer.from_pretrained(repository_id)

# Debug: Print model configuration
# print("\nModel configuration:")
# print(f"Model labels: {model.config.id2label}")
# print(f"Model num_labels: {model.config.num_labels}")

# Create the pipeline with the loaded model and tokenizer
classifier = pipeline('text-classification', 
                     model=model, 
                     tokenizer=tokenizer, 
                     device=0 if torch.cuda.is_available() else -1,
                     truncation=True,
                     max_length=512)  # Use the model's original max length

class TextRequest(BaseModel):
    text: str
    category: Optional[str] = None
    # subcategory: Optional[str] = None

class ArticleRequest(BaseModel):
    article_id: str
    title: str
    content: str

class ClassificationResponse(BaseModel):
    category: str
    # subcategory: str
    confidence: float

class ArticleResponse(BaseModel):
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
    query: Optional[str] = None
    category: Optional[str] = None
    language: str = "en"
    page_size: int = 10
    days_back: int = 7
    page: int = 1

@app.post("/articles/fetch", response_model=List[ArticleResponse])
def fetch_and_classify_articles(request: FetchArticlesRequest):
    # Fetch articles from news API with force_refresh=True to bypass cache
    articles = news_fetcher.fetch_articles(
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
        
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
        
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
            
        # Create response
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

def test_classify_article(title, content):
    if len(content) > 400:  # Limit content length to ensure we stay within token limits
        content = content[:400] + "..."
        
    text = f"{title} {content}"
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
        confidence, predicted_class = torch.max(predictions, dim=1)
        
        # Get the predicted label
        predicted_label = model.config.id2label[predicted_class.item()]
        confidence = confidence.item()
        
    return predicted_label, confidence
    

@app.get("/articles/recommendations/{user_id}", response_model=List[ArticleResponse])
async def get_recommendations(user_id: str, num_recommendations: int = 5):
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
    try:
        recommendation_system.update_user_preferences(user_id, category, confidence, article_id)
        return {"message": "User preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: TextRequest):
    try:
        # Validate input category if provided
        if request.category:
            if not validate_category(request.category):
                raise HTTPException(status_code=400, detail="Invalid category")
            request.category = map_to_main_category(request.category)

        # Process the text
        inputs = tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
        # inputs = {k: v.to(device) for k, v in inputs.items()}
        
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
    try:
        # model = models["sentiment"]["model"]
        # tokenizer = models["sentiment"]["tokenizer"]
        
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