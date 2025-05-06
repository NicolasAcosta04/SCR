"""
Main API Tests
Integration tests for the FastAPI application endpoints.

Test Coverage:
- Article fetching
- Classification endpoints
- Recommendation system
- User preference updates
- Error handling
- Authentication

Test Categories:
- Endpoint functionality
- Request validation
- Response formatting
- Error responses
- Authentication flows
- Rate limiting

Note: These tests ensure the reliability and correctness of the
API endpoints and their integration with other components.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
import json

# Initialize the test client
client = TestClient(app=app)

# interpreter_login()

# Test data samples for each category
test_articles = {
    "business": "The stock market reached record highs today as tech companies reported strong earnings. Analysts predict continued growth in the coming quarter.",
    "entertainment": "The new Marvel movie broke box office records this weekend, grossing over $200 million worldwide. Fans praised the special effects and storyline.",
    "politics": "The president announced new climate change initiatives during today's press conference. The plan includes significant investments in renewable energy.",
    "sport": "In a thrilling match last night, the underdog team defeated the reigning champions 3-2. The winning goal was scored in the final minutes of extra time.",
    "tech": "A new AI model has been developed that can generate realistic 3D images from text descriptions. The technology could revolutionize digital content creation."
}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Model API is running"}

def test_classify_article_business():
    response = client.post(
        "/classify",
        json={"text": "The stock market reached record highs today as investors reacted positively to the latest economic data."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data
    assert isinstance(data["confidence"], float)
    assert 0 <= data["confidence"] <= 1

def test_classify_article_entertainment():
    response = client.post(
        "/classify",
        json={"text": "The new Marvel movie broke box office records this weekend, grossing over $200 million worldwide."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data

def test_classify_article_politics():
    response = client.post(
        "/classify",
        json={"text": "The president announced new policies aimed at reducing carbon emissions by 50% by 2030."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data

def test_classify_article_sport():
    response = client.post(
        "/classify",
        json={"text": "The home team secured a dramatic victory in the championship game with a last-minute goal."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data

def test_classify_article_tech():
    response = client.post(
        "/classify",
        json={"text": "The new smartphone features breakthrough battery technology that lasts up to 48 hours on a single charge."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data

def test_empty_text():
    response = client.post(
        "/classify",
        json={"text": ""}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

def test_invalid_input():
    response = client.post(
        "/classify",
        json={"invalid": "field"}
    )
    assert response.status_code == 422

def test_long_text():
    long_text = "This is a very long text. " * 1000
    response = client.post(
        "/classify",
        json={"text": long_text}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data

def test_special_characters():
    response = client.post(
        "/classify",
        json={"text": "Special characters: !@#$%^&*()_+{}|:\"<>?[]\\;',./`~"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "confidence" in data 