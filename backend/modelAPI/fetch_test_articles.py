"""
Test Article Fetcher
Utility script for fetching test articles for development and testing.

Purpose:
- Fetch sample articles for testing
- Generate test datasets
- Validate article processing pipeline
- Test category distribution
- Verify content quality

Features:
- Configurable article count
- Category filtering
- Source selection
- Content validation
- Test data export

Note: This script is used for development and testing purposes only,
not for production article fetching.
"""

import json
from datetime import datetime
from news_fetcher import NewsFetcher
import os

def save_articles_to_json(articles, filename="test_articles.json"):
    """Save articles to a JSON file"""
    # Create test_data directory if it doesn't exist
    os.makedirs("test_data", exist_ok=True)
    
    filepath = os.path.join("test_data", filename)
    
    # Add metadata
    data = {
        "metadata": {
            "total_articles": len(articles),
            "categories": list(set(article["category"] for article in articles)),
            "fetched_at": datetime.now().isoformat()
        },
        "articles": articles
    }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nSaved {len(articles)} articles to {filepath}")
    print(f"Categories: {', '.join(data['metadata']['categories'])}")

def main():
    # Initialize NewsFetcher
    news_fetcher = NewsFetcher()
    
    # Delete existing test_articles.json if it exists
    test_file = os.path.join("test_data", "test_articles.json")
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"Removed existing {test_file}")
    
    # Fetch articles using the new method
    articles = news_fetcher.fetch_test_articles()
    
    # Save to JSON file
    save_articles_to_json(articles)

if __name__ == "__main__":
    main() 