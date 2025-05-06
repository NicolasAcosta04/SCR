import requests
import json
from collections import Counter
from typing import List, Dict
import matplotlib.pyplot as plt
import time
from datetime import datetime, timedelta

def fetch_articles(category: str, page_size: int = 50, timestamp: int = None) -> List[Dict]:
    """
    Fetch articles for a specific category
    Args:
        category: Category to fetch articles for
        page_size: Number of articles to fetch
        timestamp: Timestamp to use for fetching older articles
    """
    url = "http://localhost:8080/articles/fetch"
    
    payload = {
        "query": category,
        "page_size": page_size,
        "sort_by": "popularity",
        "page": 1,
        "randomize_sources": True,
        "force_refresh": True,
        "timestamp": timestamp
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch articles: {response.text}")
    
    return response.json()

def analyze_category_distribution(articles: List[Dict]) -> Dict[str, int]:
    """
    Analyze the distribution of categories in the fetched articles
    """
    categories = [article['category'].lower() for article in articles]
    return dict(Counter(categories))

def plot_distribution(distribution: Dict[str, int], category: str, run_number: int = None):
    """
    Plot the category distribution
    """
    plt.figure(figsize=(10, 6))
    categories = list(distribution.keys())
    counts = list(distribution.values())
    
    plt.bar(categories, counts)
    title = f'Category Distribution for {category} Query'
    if run_number is not None:
        title += f' (Run {run_number})'
    plt.title(title)
    plt.xlabel('Categories')
    plt.ylabel('Number of Articles')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot with run number if provided
    filename = f'category_distribution_{category.lower()}'
    if run_number is not None:
        filename += f'_run{run_number}'
    filename += '.png'
    plt.savefig(filename)
    plt.close()

def main():
    # Test categories
    test_categories = ['Politics', 'Technology', 'Business', 'Entertainment', 'Sports']
    num_runs = 3  # Number of different runs to perform
    
    # Calculate timestamps for different runs (going back in time)
    base_timestamp = int(time.time() * 1000)  # Current time in milliseconds
    timestamps = [
        base_timestamp,  # Current articles
        base_timestamp - (24 * 60 * 60 * 1000),  # 1 day ago
        base_timestamp - (48 * 60 * 60 * 1000)   # 2 days ago
    ]
    
    for run in range(num_runs):
        print(f"\n=== Run {run + 1} ===")
        timestamp = timestamps[run]
        print(f"Using timestamp: {datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        
        for category in test_categories:
            print(f"\nAnalyzing distribution for {category}...")
            try:
                # Fetch articles with the current timestamp
                articles = fetch_articles(category, timestamp=timestamp)
                print(f"Fetched {len(articles)} articles")
                
                # Analyze distribution
                distribution = analyze_category_distribution(articles)
                
                # Print results
                print("\nCategory Distribution:")
                for cat, count in distribution.items():
                    percentage = (count / len(articles)) * 100
                    print(f"{cat}: {count} articles ({percentage:.1f}%)")
                
                # Plot distribution
                plot_distribution(distribution, category, run + 1)
                print(f"Plot saved as category_distribution_{category.lower()}_run{run + 1}.png")
                
            except Exception as e:
                print(f"Error analyzing {category}: {str(e)}")
        
        # Add a small delay between runs to prevent rate limiting
        time.sleep(1)

if __name__ == "__main__":
    main() 