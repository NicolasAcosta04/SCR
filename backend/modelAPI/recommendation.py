from typing import List, Dict, Set, Optional
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import logging
from functools import lru_cache
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserPreferences:
    def __init__(self):
        self.preferences = defaultdict(lambda: {
            "count": 0, 
            "total_confidence": 0,
            "last_interaction": None,
            "categories": defaultdict(float)
        })
        self.read_articles: Set[str] = set()  # Changed to set for O(1) lookup
        self.category_weights: Dict[str, float] = {}
    
    def update_preferences(self, category: str, confidence: float, article_id: str):
        """Update user preferences with time tracking and category weighting"""
        try:
            if article_id in self.read_articles:
                return  # Prevent duplicate updates
                
            self.preferences[category]["count"] += 1
            self.preferences[category]["total_confidence"] += confidence
            self.preferences[category]["last_interaction"] = datetime.now().isoformat()
            self.read_articles.add(article_id)
            
            # Update category weights
            total_interactions = sum(pref["count"] for pref in self.preferences.values())
            for cat, pref in self.preferences.items():
                self.category_weights[cat] = pref["count"] / total_interactions
                
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
    
    def get_average_preferences(self) -> Dict[str, float]:
        """Get weighted average preferences considering recency"""
        try:
            preferences = {}
            for category, data in self.preferences.items():
                if data["count"] > 0:
                    # Calculate time decay
                    last_interaction = datetime.fromisoformat(data["last_interaction"]) if data["last_interaction"] else datetime.now()
                    time_diff = (datetime.now() - last_interaction).days
                    time_decay = np.exp(-0.1 * time_diff)  # Exponential decay
                    
                    # Calculate weighted preference
                    base_preference = data["total_confidence"] / data["count"]
                    preferences[category] = base_preference * time_decay * self.category_weights.get(category, 1.0)
                    
            return preferences
        except Exception as e:
            logger.error(f"Error calculating preferences: {str(e)}")
            return {}

class Article:
    def __init__(self, article_id: str, title: str, content: str, category: str, subcategory: str, 
                 confidence: float, source: str, url: str, published_at: str, image_url: str):
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
        
        # Parse published_at to datetime
        try:
            self.published_datetime = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except:
            self.published_datetime = datetime.now()

class RecommendationSystem:
    def __init__(self, cache_size: int = 1000):
        self.articles: Dict[str, Article] = {}
        self.user_preferences: Dict[str, UserPreferences] = defaultdict(UserPreferences)
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)  # Include bigrams for better context
        )
        self.article_vectors = None
        self.article_ids = []
        self.source_diversity = defaultdict(int)  # Track source diversity
        
    def add_article(self, article: Article):
        """Add article with cache management"""
        try:
            # Remove oldest articles if cache is full
            if len(self.articles) >= 1000:
                oldest_articles = sorted(
                    self.articles.values(), 
                    key=lambda x: x.published_datetime
                )[:100]  # Remove oldest 100 articles
                for old_article in oldest_articles:
                    self.articles.pop(old_article.article_id)
                    self.article_ids.remove(old_article.article_id)
            
            self.articles[article.article_id] = article
            self.article_ids.append(article.article_id)
            self.source_diversity[article.source] += 1
            
            # Update TF-IDF vectors
            self._update_vectors()
            
        except Exception as e:
            logger.error(f"Error adding article: {str(e)}")
    
    @lru_cache(maxsize=100)
    def _calculate_article_similarity(self, article_id1: str, article_id2: str) -> float:
        """Calculate similarity between two articles with caching"""
        try:
            if not (article_id1 in self.articles and article_id2 in self.articles):
                return 0.0
                
            vec1 = self.articles[article_id1].vector
            vec2 = self.articles[article_id2].vector
            
            if vec1 is None or vec2 is None:
                return 0.0
                
            return float(cosine_similarity(vec1, vec2)[0][0])
        except Exception as e:
            logger.error(f"Error calculating article similarity: {str(e)}")
            return 0.0
    
    def _update_vectors(self):
        """Update TF-IDF vectors with error handling"""
        try:
            if not self.articles:
                return
                
            documents = []
            for article_id in self.article_ids:
                article = self.articles[article_id]
                # Combine title, category, and content for better representation
                doc = f"{article.title} {article.category} {article.subcategory or ''} {article.content}"
                documents.append(doc)
            
            self.article_vectors = self.vectorizer.fit_transform(documents)
            
            # Store vectors in Article objects
            for i, article_id in enumerate(self.article_ids):
                self.articles[article_id].vector = self.article_vectors[i]
                
        except Exception as e:
            logger.error(f"Error updating vectors: {str(e)}")
    
    def update_user_preferences(self, user_id: str, category: str, confidence: float, article_id: str):
        """Update user preferences with error handling"""
        try:
            self.user_preferences[user_id].update_preferences(category, confidence, article_id)
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
    
    def get_recommendations(self, user_id: str, num_recommendations: int = 5) -> List[Article]:
        """Get personalized recommendations with diversity and time decay"""
        try:
            if not self.articles or not self.article_vectors:
                logger.warning("No articles available for recommendations")
                return []
            
            user = self.user_preferences[user_id]
            
            # If new user, return recent popular articles from diverse sources
            if not user.read_articles:
                return self._get_diverse_recent_articles(num_recommendations)
            
            # Calculate user profile
            read_vectors = [self.articles[aid].vector for aid in user.read_articles 
                          if aid in self.articles and self.articles[aid].vector is not None]
            
            if not read_vectors:
                return self._get_diverse_recent_articles(num_recommendations)
            
            user_profile = np.mean(read_vectors, axis=0)
            
            # Calculate article scores considering multiple factors
            article_scores = []
            for article_id in self.article_ids:
                if article_id not in user.read_articles:
                    article = self.articles[article_id]
                    
                    # Base similarity score
                    similarity = cosine_similarity(user_profile, article.vector)[0][0]
                    
                    # Time decay factor
                    time_diff = (datetime.now() - article.published_datetime).days
                    time_decay = np.exp(-0.1 * time_diff)
                    
                    # Category preference factor
                    category_weight = user.category_weights.get(article.category, 1.0)
                    
                    # Source diversity factor
                    source_factor = 1.0 / (self.source_diversity[article.source] ** 0.5)
                    
                    # Combined score
                    final_score = similarity * time_decay * category_weight * source_factor
                    
                    article_scores.append((article_id, final_score))
            
            # Sort by score and ensure source diversity
            article_scores.sort(key=lambda x: x[1], reverse=True)
            recommended_articles = []
            seen_sources = set()
            
            for article_id, _ in article_scores:
                article = self.articles[article_id]
                if len(recommended_articles) >= num_recommendations:
                    break
                    
                # Ensure source diversity
                if article.source not in seen_sources or len(seen_sources) >= num_recommendations // 2:
                    recommended_articles.append(article)
                    seen_sources.add(article.source)
            
            return recommended_articles
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return self._get_diverse_recent_articles(num_recommendations)
    
    def _get_diverse_recent_articles(self, num_articles: int) -> List[Article]:
        """Get recent articles from diverse sources"""
        try:
            # Sort articles by publish date
            recent_articles = sorted(
                self.articles.values(),
                key=lambda x: x.published_datetime,
                reverse=True
            )
            
            recommended = []
            seen_sources = set()
            
            for article in recent_articles:
                if len(recommended) >= num_articles:
                    break
                    
                # Ensure source diversity
                if article.source not in seen_sources or len(seen_sources) >= num_articles // 2:
                    recommended.append(article)
                    seen_sources.add(article.source)
            
            return recommended
            
        except Exception as e:
            logger.error(f"Error getting diverse recent articles: {str(e)}")
            return list(self.articles.values())[:num_articles]
    