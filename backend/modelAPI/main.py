from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from category_mappings import validate_category, validate_subcategory, map_to_main_category, map_to_subcategory
from recommendation import RecommendationSystem, Article
from news_fetcher import NewsFetcher

app = FastAPI()

# Initialize services
recommendation_system = RecommendationSystem()
news_fetcher = NewsFetcher()

# Load models and tokenizers
models = {
    "news": {
        "model": AutoModelForSequenceClassification.from_pretrained("nicolasacosta/roberta-base-news-classifier"),
        "tokenizer": AutoTokenizer.from_pretrained("nicolasacosta/roberta-base-news-classifier")
    },
    "sentiment": {
        "model": AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english"),
        "tokenizer": AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english")
    }
}

class TextRequest(BaseModel):
    text: str
    category: Optional[str] = None
    subcategory: Optional[str] = None

class ArticleRequest(BaseModel):
    article_id: str
    title: str
    content: str

class ClassificationResponse(BaseModel):
    category: str
    subcategory: str
    confidence: float

class ArticleResponse(BaseModel):
    article_id: str
    title: str
    content: str
    category: str
    subcategory: str
    confidence: float
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None

class FetchArticlesRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    language: str = "en"
    page_size: int = 10
    days_back: int = 7

@app.post("/articles/fetch", response_model=List[ArticleResponse])
async def fetch_and_classify_articles(request: FetchArticlesRequest):
    try:
        # Fetch articles from news API
        articles = news_fetcher.fetch_articles(
            query=request.query,
            category=request.category,
            language=request.language,
            page_size=request.page_size,
            days_back=request.days_back
        )
        
        classified_articles = []
        for article in articles:
            # Classify each article
            inputs = models["news"]["tokenizer"](
                article["content"], 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            )
            
            with torch.no_grad():
                outputs = models["news"]["model"](**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                confidence, predicted_class = torch.max(predictions, dim=1)
                
                predicted_category = models["news"]["model"].config.id2label[predicted_class.item()]
                main_category = map_to_main_category(predicted_category)
                subcategory = map_to_subcategory(predicted_category)
                
                # Create article object and add to recommendation system
                article_obj = Article(
                    article_id=article["article_id"],
                    title=article["title"],
                    content=article["content"],
                    category=main_category,
                    confidence=confidence.item()
                )
                recommendation_system.add_article(article_obj)
                
                # Create response
                classified_articles.append(ArticleResponse(
                    article_id=article["article_id"],
                    title=article["title"],
                    content=article["content"],
                    category=main_category,
                    subcategory=subcategory,
                    confidence=confidence.item(),
                    source=article["source"],
                    url=article["url"],
                    published_at=article["published_at"]
                ))
        
        return classified_articles
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                subcategory=map_to_subcategory(article.category),
                confidence=article.confidence
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
        # Validate input category and subcategory if provided
        if request.category:
            if not validate_category(request.category):
                raise HTTPException(status_code=400, detail="Invalid category")
            request.category = map_to_main_category(request.category)
        
        if request.subcategory:
            if not validate_subcategory(request.subcategory):
                raise HTTPException(status_code=400, detail="Invalid subcategory")
            request.subcategory = map_to_subcategory(request.subcategory)

        # Use news classification model
        model = models["news"]["model"]
        tokenizer = models["news"]["tokenizer"]
        
        # Tokenize and get predictions
        inputs = tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence, predicted_class = torch.max(predictions, dim=1)
            
            # Get category and subcategory from model's prediction
            predicted_category = model.config.id2label[predicted_class.item()]
            main_category = map_to_main_category(predicted_category)
            subcategory = map_to_subcategory(predicted_category)
            
            return ClassificationResponse(
                category=main_category,
                subcategory=subcategory,
                confidence=confidence.item()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-sentiment")
async def analyze_sentiment(request: TextRequest):
    try:
        model = models["sentiment"]["model"]
        tokenizer = models["sentiment"]["tokenizer"]
        
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
    uvicorn.run(app, host="0.0.0.0", port=8000)