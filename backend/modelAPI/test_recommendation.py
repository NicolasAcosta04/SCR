import sys
import os
import json
from datetime import datetime, timedelta
from recommendation import RecommendationSystem, Article
from category_mappings import SUBCATEGORY_MAPPINGS, MAIN_CATEGORIES
from collections import defaultdict
from main import test_classify_article


def classify_article(title, content):
    # Call a the classification method from main.py
    predicted_label, confidence = test_classify_article(title, content)
        
    return predicted_label, confidence

def load_test_articles(filename="test_articles.json"):
    """Load articles from the test data JSON file"""
    try:
        filepath = os.path.join("test_data", filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
            print(f"\nLoaded {data['metadata']['total_articles']} articles")
            print(f"Categories: {', '.join(data['metadata']['categories'])}")
            print(f"Fetched at: {data['metadata']['fetched_at']}")
            return data['articles']
    except Exception as e:
        print(f"Error loading test articles: {str(e)}")
        return []

def create_article_objects(articles_data):
    """Convert article dictionaries to Article objects, using model classification"""
    article_objs = []
    for article in articles_data:
        predicted_category, predicted_confidence = classify_article(article["title"], article["content"])
        article_objs.append(Article(
            article_id=article["article_id"],
            title=article["title"],
            content=article["content"],
            category=predicted_category,
            subcategory=None,  # We'll skip subcategory for this test
            confidence=predicted_confidence,
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
    for article in recommendations:
        if article.category == user_category:
            correct += 1
    return correct / len(recommendations) if recommendations else 0.0

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
    # Convert to Article objects (using model classification)
    print("\nClassifying articles with AI model...")
    articles = create_article_objects(articles_data)
    # Add articles to recommendation system
    print("\nAdding articles to recommendation system...")
    for article in articles:
        rec_system.add_article(article)
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
        # Calculate accuracy
        accuracy = evaluate_recommendations(recommendations, user_data["category"])
        results[user_id]["accuracy"] = accuracy
        # Print recommendations and their categories
        for i, article in enumerate(recommendations, 1):
            print(f"\n{i} {article.title}")
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