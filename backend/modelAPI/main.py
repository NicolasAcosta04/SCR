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
repository_id = "nicolasacosta/roberta-base_ag_news"

# Load model config
config = AutoConfig.from_pretrained(repository_id, num_labels=4)

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Load the model and tokenizer directly without PEFT
model = AutoModelForSequenceClassification.from_pretrained(repository_id, config=config)
model = model.to(device)  # Move model to device
tokenizer = AutoTokenizer.from_pretrained(repository_id, use_fast=False)

# Debug: Print model configuration
print("\nModel configuration:")
print(f"Model labels: {model.config.id2label}")
print(f"Model num_labels: {model.config.num_labels}")

# Create the pipeline with the loaded model and tokenizer
classifier = pipeline('text-classification', model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

# Test the model with a sample text
test_title = "Stock Market Update"
test_description = "Major gains in tech sector"
test_content = "The stock market reached new heights today as tech companies led gains."
test_combined = f"{test_title} {test_description} {test_content}"
test_inputs = tokenizer(test_combined, return_tensors="pt", truncation=True, max_length=512)
test_inputs = {k: v.to(device) for k, v in test_inputs.items()}

result = classifier(test_combined)
print(f"Predicted label: {result[0]['label']}")
print(f"Confidence: {result[0]['score']}")

with torch.no_grad():
    test_outputs = model(**test_inputs)
    test_predictions = torch.nn.functional.softmax(test_outputs.logits, dim=-1)
    print("\nTest prediction:")
    print(f"Input text: {test_combined}")
    print(f"Raw predictions: {test_predictions}")
    print(f"Predicted class: {torch.argmax(test_predictions).item()}")
    print(f"Predicted label: {model.config.id2label[torch.argmax(test_predictions).item()]}")
    print(f"Confidence: {torch.max(test_predictions).item()}")



# models = {
#     "news": {
#         "model": model,
#         "tokenizer": tokenizer,
#         "pipeline": classifier
#     },
#     "sentiment": {
#         "model": AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english"),
#         "tokenizer": AutoTokenizer.from_pretrained("distilbert-base-uncased-finetuned-sst-2-english", use_fast=False)
#     }
# }

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
    # subcategory: str
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

@app.post("/articles/fetch", response_model=List[ArticleResponse])
def fetch_and_classify_articles(request: FetchArticlesRequest):
    # Fetch articles from news API
    articles = news_fetcher.fetch_articles(
        query=request.query,
        category=request.category,
        language=request.language,
        page_size=request.page_size,
        days_back=request.days_back
    )
    
    print(f"\nArticles: {articles}")
    
    classified_articles = []
    for article in articles:
        # Combine title, description, and content for better context
        text = f"{article['title']} {article.get('description', '')} {article['content']}"
        
        # Get raw model outputs for debugging
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}  # Move inputs to device
        
        print(f"\nProcessing article: {article['title']}")
        print(f"Input text length: {len(text)}")
        print(f"Input shape: {inputs['input_ids'].shape}")
        
        with torch.no_grad():
            # Get raw model outputs
            outputs = model(**inputs)
            logits = outputs.logits
            print(f"Raw logits shape: {logits.shape}")
            print(f"Raw logits: {logits}")
            
            # Calculate probabilities
            probs = torch.nn.functional.softmax(logits, dim=-1)
            print(f"Probabilities: {probs}")
            
            # Get prediction
            confidence, predicted_class = torch.max(probs, dim=1)
            print(f"Predicted class index: {predicted_class.item()}")
            print(f"Confidence: {confidence.item()}")
            
            # Map to label
            predicted_label = model.config.id2label[predicted_class.item()]
            print(f"Predicted label: {predicted_label}")
        
        # Create article object and add to recommendation system
        article_obj = Article(
            article_id=article["article_id"],
            title=article["title"],
            content=article["content"],
            category=predicted_label.lower(),
            confidence=confidence.item()
        )
        recommendation_system.add_article(article_obj)
        
        # Create response
        classified_articles.append(ArticleResponse(
            article_id=article["article_id"],
            title=article["title"],
            content=article["content"],
            category=predicted_label.lower(),
            confidence=confidence.item(),
            source=article["source"],
            url=article["url"],
            published_at=article["published_at"],
            image_url=article["image_url"]
        ))
    
    return classified_articles

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
                # subcategory=map_to_subcategory(article.category),
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
        # Validate input category if provided
        if request.category:
            if not validate_category(request.category):
                raise HTTPException(status_code=400, detail="Invalid category")
            request.category = map_to_main_category(request.category)

        # Process the text
        inputs = tokenizer(request.text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
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