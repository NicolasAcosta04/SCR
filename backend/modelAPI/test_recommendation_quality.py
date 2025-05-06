import unittest
from recommendation import RecommendationSystem, Article
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np
import logging
import asyncio
from news_fetcher import NewsFetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRecommendationQuality(unittest.TestCase):
    def setUp(self):
        self.recommendation_system = RecommendationSystem()
        self.news_fetcher = NewsFetcher()
        self.test_users = {
            'user_politics': {'Politics': 1.0},
            'user_tech': {'Technology': 1.0},
            'user_business': {'Business': 1.0},
            'user_entertainment': {'Entertainment': 1.0},
            'user_sports': {'Sports': 1.0}
        }
        
        # Create test data directory if it doesn't exist
        os.makedirs('test_data', exist_ok=True)
        
        # Fetch real articles for each category
        self._fetch_test_articles()
        
    def _fetch_test_articles(self):
        """Fetch real articles for each category"""
        category_queries = {
            'Politics': ['election', 'congress', 'government', 'policy', 'democrat', 'republican'],
            'Technology': ['artificial intelligence', 'software', 'hardware', 'innovation', 'digital'],
            'Business': ['market', 'economy', 'finance', 'stock', 'investment'],
            'Entertainment': ['movie', 'music', 'celebrity', 'film', 'entertainment'],
            'Sports': ['football', 'basketball', 'soccer', 'sport', 'championship']
        }
        
        async def fetch_category_articles(category: str):
            try:
                # Use multiple queries for each category to get diverse content
                all_articles = []
                for query in category_queries[category]:
                    articles = await self.news_fetcher.fetch_articles(
                        query=query,
                        page_size=10,  # 10 articles per query
                        days_back=14,  # Articles from the last 14 days
                        force_refresh=True
                    )
                    all_articles.extend(articles)
                
                # Remove duplicates based on article_id
                unique_articles = {article["article_id"]: article for article in all_articles}.values()
                logger.info(f"Fetched {len(unique_articles)} unique articles for category: {category}")
                return list(unique_articles)
            except Exception as e:
                logger.error(f"Error fetching articles for {category}: {str(e)}")
                return []
        
        # Fetch articles for all categories
        for category in category_queries.keys():
            articles = asyncio.run(fetch_category_articles(category))
            for article in articles:
                article_obj = Article(
                    article_id=article["article_id"],
                    title=article["title"],
                    content=article["content"],
                    category=category,  # Use the category we searched for
                    confidence=0.9,     # High confidence since we searched by category
                    source=article["source"],
                    url=article["url"],
                    published_at=article["published_at"],
                    image_url=article["image_url"]
                )
                self.recommendation_system.add_article(article_obj)
        
        # Force vector update after adding all articles
        self.recommendation_system._update_vectors()
        logger.info(f"Added {len(self.recommendation_system.articles)} articles to the system")
        
    def test_recommendation_quality(self):
        """Test the quality of recommendations for users with different preferences"""
        results = {}
        
        for user_id, preferences in self.test_users.items():
            print(f"\nTesting recommendations for {user_id}")
            
            # Update user preferences by simulating article reads
            preferred_category = list(preferences.keys())[0]
            print(f"Adding articles to user preferences for category: {preferred_category}")
            
            # Find articles in the preferred category
            category_articles = [
                article_id for article_id, article in self.recommendation_system.articles.items()
                if article.category == preferred_category
            ]
            
            # Add more articles to user preferences (up to 20 instead of 12)
            for i, article_id in enumerate(category_articles[:20]):
                # Add each article multiple times to strengthen the preference
                for _ in range(3):  # Add each article 3 times
                    self.recommendation_system.update_user_preferences(
                        user_id=user_id,
                        category=preferred_category,
                        confidence=1.0,
                        article_id=article_id
                    )
            
            # Get recommendations for the user
            recommendations = self.recommendation_system.get_recommendations(
                user_id=user_id,
                num_recommendations=10
            )
            
            if not recommendations:
                logger.error(f"No recommendations returned for {user_id}")
                continue
            
            # Analyze category distribution
            category_counts = {}
            for article in recommendations:
                category = article.category
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Calculate preference match score
            preference_match = category_counts.get(preferred_category, 0) / len(recommendations)
            
            results[user_id] = {
                'category_distribution': category_counts,
                'preference_match': preference_match,
                'recommendations': [
                    {
                        'title': article.title,
                        'category': article.category,
                        'confidence': article.confidence
                    } for article in recommendations
                ]
            }
            
            # Print results
            print(f"Preferred category: {preferred_category}")
            print("Category distribution:")
            for category, count in category_counts.items():
                print(f"  {category}: {count} articles ({count/len(recommendations)*100:.1f}%)")
            print(f"Preference match score: {preference_match:.2f}")
        
        if not results:
            self.fail("No recommendations were generated for any user")
        
        # Save detailed results
        with open('test_data/recommendation_quality_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Plot results
        self.plot_recommendation_quality(results)
        
    def plot_recommendation_quality(self, results: Dict):
        """Plot the recommendation quality results"""
        plt.figure(figsize=(15, 10))
        
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot 1: Category Distribution
        categories = set()
        for result in results.values():
            categories.update(result['category_distribution'].keys())
        
        categories = sorted(list(categories))
        x = np.arange(len(results))
        width = 0.15
        
        for i, category in enumerate(categories):
            values = [results[user_id]['category_distribution'].get(category, 0) 
                     for user_id in results.keys()]
            ax1.bar(x + i*width, values, width, label=category)
        
        ax1.set_ylabel('Number of Articles')
        ax1.set_title('Category Distribution in Recommendations')
        ax1.set_xticks(x + width*2)
        ax1.set_xticklabels([user_id.replace('user_', '') for user_id in results.keys()])
        ax1.legend()
        
        # Plot 2: Preference Match Scores
        match_scores = [result['preference_match'] for result in results.values()]
        ax2.bar(results.keys(), match_scores)
        ax2.set_ylabel('Preference Match Score')
        ax2.set_title('Preference Match Scores by User')
        ax2.set_ylim(0, 1)
        
        # Add value labels
        for i, score in enumerate(match_scores):
            ax2.text(i, score, f'{score:.2f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('test_data/recommendation_quality_analysis.png')
        plt.close()

if __name__ == '__main__':
    unittest.main() 