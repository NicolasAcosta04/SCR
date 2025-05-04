import json
import random
import os
from datetime import datetime, timezone

def add_confidence_to_articles():
    """Add confidence levels to existing articles in test_articles.json"""
    # Path to the test articles file
    filepath = os.path.join("test_data", "test_articles.json")
    
    # Read the existing JSON file
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Add confidence to each article and fix datetime
    for article in data["articles"]:
        article["confidence"] = round(random.uniform(0.85, 0.99), 2)
        
        # Fix datetime format
        if "published_at" in article:
            try:
                # Try to parse the existing datetime
                dt = datetime.fromisoformat(article["published_at"].replace('Z', '+00:00'))
                # Ensure it's timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                # Convert to ISO format with timezone
                article["published_at"] = dt.isoformat()
            except (ValueError, AttributeError):
                # If parsing fails, use current time with timezone
                article["published_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save the updated data back to the file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nAdded confidence levels to {len(data['articles'])} articles")
    print(f"Categories: {', '.join(data['metadata']['categories'])}")

if __name__ == "__main__":
    add_confidence_to_articles() 