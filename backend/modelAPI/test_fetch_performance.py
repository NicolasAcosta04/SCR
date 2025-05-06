import requests
import time
from typing import List, Dict
import statistics
from datetime import datetime
import matplotlib.pyplot as plt

def fetch_articles(category: str, page_size: int = 50, timestamp: int = None) -> List[Dict]:
    """
    Fetch articles for a specific category
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

def measure_fetch_time(category: str, num_runs: int = 5) -> Dict:
    """
    Measure the time taken to fetch articles for a category over multiple runs
    """
    times = []
    article_counts = []
    
    for run in range(num_runs):
        start_time = time.time()
        articles = fetch_articles(category)
        end_time = time.time()
        
        fetch_time = end_time - start_time
        times.append(fetch_time)
        article_counts.append(len(articles))
        
        # Small delay between runs to prevent rate limiting
        time.sleep(0.5)
    
    return {
        'category': category,
        'avg_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
        'avg_articles': statistics.mean(article_counts)
    }

def plot_performance_results(results: List[Dict]):
    """
    Plot the performance results
    """
    categories = [r['category'] for r in results]
    avg_times = [r['avg_time'] for r in results]
    std_devs = [r['std_dev'] for r in results]
    
    plt.figure(figsize=(12, 6))
    
    # Create bar chart with error bars
    bars = plt.bar(categories, avg_times, yerr=std_devs, capsize=5)
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}s',
                ha='center', va='bottom')
    
    plt.title('Article Fetch Performance by Category')
    plt.xlabel('Category')
    plt.ylabel('Average Fetch Time (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('fetch_performance.png')
    plt.close()

def main():
    # Test categories
    test_categories = ['Politics', 'Technology', 'Business', 'Entertainment', 'Sports']
    num_runs = 5  # Number of runs per category
    
    print(f"Starting performance test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {len(test_categories)} categories with {num_runs} runs each\n")
    
    results = []
    
    for category in test_categories:
        print(f"\nTesting {category}...")
        try:
            result = measure_fetch_time(category, num_runs)
            results.append(result)
            
            print(f"Results for {category}:")
            print(f"  Average time: {result['avg_time']:.2f} seconds")
            print(f"  Min time: {result['min_time']:.2f} seconds")
            print(f"  Max time: {result['max_time']:.2f} seconds")
            print(f"  Standard deviation: {result['std_dev']:.2f} seconds")
            print(f"  Average articles fetched: {result['avg_articles']:.1f}")
            
        except Exception as e:
            print(f"Error testing {category}: {str(e)}")
    
    # Plot results
    plot_performance_results(results)
    print("\nPerformance plot saved as 'fetch_performance.png'")
    
    # Print summary
    print("\nSummary:")
    print("-" * 50)
    print(f"{'Category':<15} {'Avg Time (s)':<15} {'Std Dev (s)':<15} {'Avg Articles':<15}")
    print("-" * 50)
    for result in results:
        print(f"{result['category']:<15} {result['avg_time']:<15.2f} {result['std_dev']:<15.2f} {result['avg_articles']:<15.1f}")

if __name__ == "__main__":
    main() 