"""
Model Utilities Module
Helper functions for model operations and text processing.

Key Features:
- Text preprocessing
- Model input preparation
- Confidence score calculation
- Category mapping
- Error handling for model operations

Dependencies:
- Transformers for model operations
- PyTorch for tensor operations
- NLTK for text processing

Note: This module provides common utilities used across the model API
to ensure consistent text processing and model interaction.
"""

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoConfig

# Initialize model and tokenizer
repository_id = "nicolasacosta/roberta-base_bbc-news"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model and tokenizer
config = AutoConfig.from_pretrained(repository_id)
model = AutoModelForSequenceClassification.from_pretrained(repository_id, config=config).to(device)
tokenizer = AutoTokenizer.from_pretrained(repository_id, use_fast=False)

def test_classify_article(title, content):
    """Classify an article using the model"""
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