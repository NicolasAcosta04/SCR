from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from category_mappings import validate_category, validate_subcategory, map_to_main_category, map_to_subcategory

app = FastAPI()

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

class ClassificationResponse(BaseModel):
    category: str
    subcategory: str
    confidence: float

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