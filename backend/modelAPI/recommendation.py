from typing import List, Dict
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class UserPreferences:
    def __init__(self):
        self.preferences = defaultdict(lambda: {"count": 0, "total_confidence": 0})
        self.read_articles: List[str] = []  # Store article IDs that user has read
    
    def update_preferences(self, category: str, confidence: float, article_id: str):
        self.preferences[category]["count"] += 1
        self.preferences[category]["total_confidence"] += confidence
        self.read_articles.append(article_id)
    
    def get_average_preferences(self) -> Dict[str, float]:
        return {
            category: data["total_confidence"] / data["count"] 
            for category, data in self.preferences.items() 
            if data["count"] > 0
        }

class Article:
    def __init__(self, article_id: str, title: str, content: str, category: str, subcategory: str, confidence: float, source: str, url: str, published_at: str, image_url: str):
        self.article_id = article_id
        self.title = title
        self.content = content
        self.category = category
        self.subcategory = subcategory
        self.confidence = confidence
        self.source = source
        self.url = url
        self.published_at = published_at
        self.image_url = image_url
        self.vector = None  # Will store TF-IDF vector

class RecommendationSystem:
    def __init__(self):
        self.articles: Dict[str, Article] = {}  # Store articles by ID
        self.user_preferences: Dict[str, UserPreferences] = defaultdict(UserPreferences)
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        self.article_vectors = None  # Will store TF-IDF vectors for all articles
        self.article_ids = []  # Keep track of article IDs in order
    
    def add_article(self, article: Article):
        self.articles[article.article_id] = article
        self.article_ids.append(article.article_id)
        
        # Update TF-IDF vectors
        self._update_vectors()
    
    def _update_vectors(self):
        """Update TF-IDF vectors for all articles"""
        if not self.articles:
            return
            
        # Prepare documents for vectorization
        documents = []
        for article_id in self.article_ids:
            article = self.articles[article_id]
            # Combine title and content for better representation
            documents.append(f"{article.title} {article.content}")
        
        # Fit and transform documents
        self.article_vectors = self.vectorizer.fit_transform(documents)
        
        # Store vectors in Article objects
        for i, article_id in enumerate(self.article_ids):
            self.articles[article_id].vector = self.article_vectors[i]
    
    def update_user_preferences(self, user_id: str, category: str, confidence: float, article_id: str):
        self.user_preferences[user_id].update_preferences(category, confidence, article_id)
    
    def get_recommendations(self, user_id: str, num_recommendations: int = 5) -> List[Article]:
        if not self.articles or not self.article_vectors:
            return []
        
        user = self.user_preferences[user_id]
        
        # Create user profile vector based on read articles
        if not user.read_articles:
            # If user hasn't read any articles, return most recent articles
            return [self.articles[aid] for aid in self.article_ids[-num_recommendations:]]
        
        # Calculate user profile vector as average of read articles' vectors
        read_vectors = [self.articles[aid].vector for aid in user.read_articles]
        user_profile = np.mean(read_vectors, axis=0)
        
        # Calculate cosine similarity between user profile and all articles
        similarities = cosine_similarity(user_profile, self.article_vectors).flatten()
        
        # Create list of (article_id, similarity) tuples
        article_similarities = list(zip(self.article_ids, similarities))
        
        # Sort by similarity and filter out already read articles
        article_similarities.sort(key=lambda x: x[1], reverse=True)
        recommended_articles = []
        
        for article_id, _ in article_similarities:
            if article_id not in user.read_articles:
                recommended_articles.append(self.articles[article_id])
                if len(recommended_articles) >= num_recommendations:
                    break
        
        return recommended_articles 
    