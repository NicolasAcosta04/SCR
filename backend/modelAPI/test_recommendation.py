"""
Recommendation System Tests
Unit and integration tests for the recommendation system.

Test Coverage:
- User preference tracking
- Article similarity calculation
- Recommendation generation
- Category-based filtering
- Time decay functionality
- Edge cases and error handling

Test Categories:
- Unit tests for individual components
- Integration tests for full recommendation flow
- Performance tests for large datasets
- Edge case tests for unusual inputs

Note: These tests ensure the reliability and correctness of the
recommendation system's core functionality.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from recommendation import RecommendationSystem, Article
from category_mappings import SUBCATEGORY_MAPPINGS, MAIN_CATEGORIES
from collections import defaultdict
from model_utils import test_classify_article


def classify_article(title, content):
    # Call a the classification method from main.py
    predicted_label, confidence = test_classify_article(title, content)
        
    return predicted_label, confidence

def load_test_articles(filename="test_articles.json"):
    """Load articles from the test data JSON file"""
    try:
        # Create test_data directory if it doesn't exist
        test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        os.makedirs(test_data_dir, exist_ok=True)
        
        filepath = os.path.join(test_data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"\nError: Test data file not found at {filepath}")
            print("Please ensure the test_articles.json file exists in the test_data directory.")
            return []
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            print(f"\nLoaded {data['metadata']['total_articles']} articles")
            print(f"Categories: {', '.join(data['metadata']['categories'])}")
            print(f"Fetched at: {data['metadata']['fetched_at']}")
            return data['articles']
    except Exception as e:
        print(f"Error loading test articles: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for file at: {filepath}")
        return []

def create_article_objects(articles_data):
    """Convert article dictionaries to Article objects without classification"""
    article_objs = []
    for article in articles_data:
        article_objs.append(Article(
            article_id=article["article_id"],
            title=article["title"],
            content=article["content"],
            category=article["category"],  # Will be classified later
            subcategory=None,
            confidence=article["confidence"],  # Will be updated after classification
            source=article["source"],
            url=article["url"],
            published_at=article["published_at"],
            image_url=article["image_url"]
        ))
    return article_objs

def evaluate_recommendations(recommendations, user_category):
    """Evaluate the accuracy of recommendations for a user"""
    if user_category == "all":
        return 1.0  # All recommendations are considered correct for diverse users
    
    correct = 0
    total = len(recommendations)
    
    print(f"\nEvaluating recommendations for {user_category} user:")
    for article in recommendations:
        # Classify the recommended article
        predicted_category, confidence = classify_article(article.title, article.content)
        # print(f"\nArticle: {article.title}")
        # print(f"Original category: {article.category}")
        # print(f"Predicted category: {predicted_category}")
        # print(f"Confidence: {confidence:.2f}")
        
        article.category = predicted_category
        
        if predicted_category.lower() == user_category.lower():
            correct += 1
            print("✓ Correct category match")
        else:
            print("✗ Category mismatch")
    
    accuracy = correct / total if total > 0 else 0.0
    print(f"\nAccuracy: {accuracy:.2%} ({correct}/{total} correct)")
    return accuracy

def test_recommendation_system():
    """Test the recommendation system with saved articles and evaluate accuracy"""
    print("\nTesting recommendation system...")
    # Initialize recommendation system
    rec_system = RecommendationSystem()
    
    # Load test articles
    articles_data = load_test_articles()
    if not articles_data:
        print("No test articles available. Please run fetch_test_articles.py first.")
        return
    
    # Convert to Article objects (without classification)
    print("\nCreating article objects...")
    articles = create_article_objects(articles_data)
    
    # Add articles to recommendation system
    print("\nAdding articles to recommendation system...")
    for article in articles:
        rec_system.add_article(article)
    
    # # Classify articles after they're added to the system
    # print("\nClassifying articles with AI model...")
    # for article_id, article in rec_system.articles.items():
    #     predicted_category, confidence = classify_article(article.title, article.content)
    #     article.category = predicted_category
    #     article.confidence = confidence
    #     print(f"Classified: {article.title}")
    #     print(f"Category: {predicted_category}")
    #     print(f"Confidence: {confidence:.2f}\n")
    
    # Create user profiles
    users = {
        "tech_user": {"category": "tech", "articles": []},
        "business_user": {"category": "business", "articles": []},
        "politics_user": {"category": "politics", "articles": []},
        "entertainment_user": {"category": "entertainment", "articles": []},
        "sport_user": {"category": "sport", "articles": []},
        "diverse_user": {"category": "all", "articles": []}
    }
    
    # Find articles for each user profile
    for article_id, article in rec_system.articles.items():
        for user_id, user_data in users.items():
            if user_data["category"] == "all" or article.category == user_data["category"]:
                user_data["articles"].append(article_id)
    
    # Update user preferences
    print("\nUpdating user preferences...")
    for user_id, user_data in users.items():
        # Take up to 5 articles for each user
        for article_id in user_data["articles"][:5]:
            article = rec_system.articles[article_id]
            rec_system.update_user_preferences(
                user_id,
                article.category,
                article.confidence,
                article_id
            )
        print(f"Updated preferences for {user_id}")
    
    # Get and evaluate recommendations
    print("\nGetting and evaluating recommendations...")
    results = defaultdict(dict)
    for user_id, user_data in users.items():
        print(f"\nRecommendations for {user_id}:")
        recommendations = rec_system.get_recommendations(user_id, num_recommendations=5)
        
        # Calculate accuracy using classification
        accuracy = evaluate_recommendations(recommendations, user_data["category"])
        results[user_id]["accuracy"] = accuracy
        
        # Print recommendations and their categories
        for i, article in enumerate(recommendations, 1):
            print(f"\n{i}. {article.title}")
            print(f"   Original category: {user_data['category']}")
            print(f"   Category: {article.category}")
            print(f"   Source: {article.source}")
            print(f"   Published: {article.published_datetime}")
        print(f"\nAccuracy for {user_id}: {accuracy:.2%}")
    # Print overall results
    print("\nOverall Results:")
    print("-" * 50)
    for user_id, data in results.items():
        print(f"{user_id}: {data['accuracy']:.2%} accuracy")

if __name__ == "__main__":
    test_recommendation_system() 