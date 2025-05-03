import os
import json
from datetime import datetime, timedelta
from news_fetcher import NewsFetcher
from category_mappings import training_collector, SUBCATEGORY_MAPPINGS, subcategory_classifier
import time

def collect_training_data():
    """Collect training data from NewsAPI for each subcategory."""
    news_fetcher = NewsFetcher()
    
    # Get all subcategories
    subcategories = list(SUBCATEGORY_MAPPINGS.keys())
    
    # Collect articles for each subcategory
    for subcategory in subcategories:
        print(f"Collecting articles for {subcategory}...")
        
        # Use subcategory name as query
        articles = news_fetcher.fetch_articles(
            query=subcategory,
            language="en",
            page_size=50,  # Get more articles for better training
            days_back=30,  # Look back 30 days
            force_refresh=True
        )
        
        # Add articles to training data
        for article in articles:
            # Combine title and content for better context
            text = f"{article['title']} {article['content']}"
            training_collector.add_article(text, subcategory)
        
        print(f"Added {len(articles)} articles for {subcategory}")
        
        # Sleep to avoid rate limiting
        time.sleep(1)

def main():
    # Create training data directory if it doesn't exist
    if not os.path.exists("training_data"):
        os.makedirs("training_data")
    
    # Collect training data
    collect_training_data()
    
    # Print statistics
    training_data = training_collector.get_training_data()
    print("\nTraining data statistics:")
    for category, texts in training_data.items():
        print(f"{category}: {len(texts)} articles")
    
    # Retrain and save the model
    print("\nRetraining model with new data...")
    subcategory_classifier.retrain()
    print("Model retrained and saved successfully!")

if __name__ == "__main__":
    main() 