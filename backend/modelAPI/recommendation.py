"""
News Recommendation System
Implements a content-based recommendation system with user preference tracking,
article similarity calculation, and diversity-aware article selection.
"""

from typing import List, Dict, Set, Optional
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timezone
import logging
from functools import lru_cache
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserPreferences:
    """
    Manages user preferences and reading history
    Tracks category preferences, article interactions, and implements time decay
    """
    def __init__(self):
        # Initialize preference tracking with default values
        self.preferences = defaultdict(lambda: {
            "count": 0, 
            "total_confidence": 0,
            "last_interaction": None,
            "categories": defaultdict(float)
        })
        self.read_articles = set()  # Set for O(1) lookup of read articles
        self.category_weights = defaultdict(float)  # Weights for different categories
    
    def update_preferences(self, category: str, confidence: float, article_id: str):
        """
        Update user preferences with time tracking and category weighting
        Args:
            category: Article category
            confidence: Classification confidence
            article_id: Unique article identifier
        """
        try:
            if article_id in self.read_articles:
                return  # Prevent duplicate updates
                
            # Update preference statistics
            self.preferences[category]["count"] += 1
            self.preferences[category]["total_confidence"] += confidence
            self.preferences[category]["last_interaction"] = datetime.now(timezone.utc).isoformat()
            self.read_articles.add(article_id)
            
            # Update category weights based on interaction frequency
            total_interactions = sum(pref["count"] for pref in self.preferences.values())
            if total_interactions > 0:  # Prevent division by zero
                for cat, pref in self.preferences.items():
                    self.category_weights[cat] = pref["count"] / total_interactions
                
        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
    
    def get_average_preferences(self) -> Dict[str, float]:
        """
        Calculate weighted average preferences considering recency
        Returns:
            Dictionary mapping categories to weighted preference scores
        """
        try:
            preferences = {}
            for category, data in self.preferences.items():
                if data["count"] > 0:
                    # Calculate time decay factor
                    last_interaction = datetime.fromisoformat(data["last_interaction"]) if data["last_interaction"] else datetime.now(timezone.utc)
                    if last_interaction.tzinfo is None:
                        last_interaction = last_interaction.replace(tzinfo=timezone.utc)
                    time_diff = (datetime.now(timezone.utc) - last_interaction).days
                    time_decay = np.exp(-0.1 * time_diff)  # Exponential decay
                    
                    # Calculate weighted preference score
                    base_preference = data["total_confidence"] / data["count"]
                    preferences[category] = base_preference * time_decay * self.category_weights.get(category, 1.0)
                    
            return preferences
        except Exception as e:
            logger.error(f"Error calculating preferences: {str(e)}")
            return {}

class Article:
    """
    Represents a news article with metadata and vector representation
    """
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
        self.vector = None  # TF-IDF vector representation
        
        # Parse published_at to timezone-aware datetime
        try:
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            self.published_datetime = dt
        except:
            self.published_datetime = datetime.now(timezone.utc)

class RecommendationSystem:
    """
    Main recommendation system implementing content-based filtering
    with diversity awareness and user preference tracking
    """
    def __init__(self, cache_size: int = 1000):
        self.articles: Dict[str, Article] = {}  # Article storage
        self.user_preferences: Dict[str, UserPreferences] = defaultdict(UserPreferences)  # User preference tracking
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)  # Include bigrams for better context
        )
        self.article_vectors = None  # TF-IDF vectors for all articles
        self.article_ids = []  # Ordered list of article IDs
        self.source_diversity = defaultdict(int)  # Track source diversity
        self.is_vectorizer_fitted = False  # Track vectorizer state
        
    def add_article(self, article: Article):
        """
        Add article to the system with cache management
        Args:
            article: Article object to add
        """
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
            
            # Add new article
            self.articles[article.article_id] = article
            self.article_ids.append(article.article_id)
            self.source_diversity[article.source] += 1
            
            # Update TF-IDF vectors
            self._update_vectors()
            
        except Exception as e:
            logger.error(f"Error adding article: {str(e)}")
    
    @lru_cache(maxsize=100)
    def _calculate_article_similarity(self, article_id1: str, article_id2: str) -> float:
        """
        Calculate cosine similarity between two articles with caching
        Args:
            article_id1: First article ID
            article_id2: Second article ID
        Returns:
            Similarity score between 0 and 1
        """
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
        """
        Update TF-IDF vectors for all articles
        Handles vectorizer fitting and transformation
        """
        try:
            if not self.articles:
                return
                
            # Prepare documents for vectorization
            documents = []
            valid_article_ids = []
            for article_id in self.article_ids:
                article = self.articles[article_id]
                # Combine title, category, and content for better representation
                doc = f"{article.title} {article.category} {article.subcategory or ''} {article.content}"
                if doc.strip():  # Only add non-empty documents
                    documents.append(doc)
                    valid_article_ids.append(article_id)
            
            if not documents:
                logger.warning("No valid documents to vectorize")
                return
            
            try:
                if not self.is_vectorizer_fitted:
                    # First time fitting the vectorizer
                    vectors = self.vectorizer.fit_transform(documents)
                    self.is_vectorizer_fitted = True
                else:
                    # Transform new documents using existing vocabulary
                    vectors = self.vectorizer.transform(documents)
                
                # Convert to dense array for easier manipulation
                dense_vectors = vectors.toarray()
                
                # Store vectors in Article objects
                for i, article_id in enumerate(valid_article_ids):
                    if i < dense_vectors.shape[0]:  # Ensure index is within bounds
                        self.articles[article_id].vector = dense_vectors[i].reshape(1, -1)
                
                self.article_vectors = vectors
                
            except Exception as e:
                logger.error(f"Error in vectorization: {str(e)}")
                # Reset vectorizer if there's an error
                self.is_vectorizer_fitted = False
                self.vectorizer = TfidfVectorizer(
                    stop_words='english',
                    max_features=5000,
                    ngram_range=(1, 2)
                )
                
        except Exception as e:
            logger.error(f"Error updating vectors: {str(e)}")
            # Reset vectorizer state
            self.is_vectorizer_fitted = False
    
    def update_user_preferences(self, user_id: str, category: str, confidence: float, article_id: str):
        """
        Update user preferences based on article interaction
        Args:
            user_id: User identifier
            category: Article category
            confidence: Classification confidence
            article_id: Article identifier
        """
        try:
            self.user_preferences[user_id].update_preferences(category, confidence, article_id)
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
    
    def get_recommendations(self, user_id: str, num_recommendations: int = 5) -> List[Article]:
        """
        Get personalized article recommendations
        Args:
            user_id: User identifier
            num_recommendations: Number of recommendations to return
        Returns:
            List of recommended Article objects
        """
        try:
            if not self.articles:
                logger.warning("No articles available for recommendations")
                return []
            
            if self.article_vectors is None:
                logger.warning("No article vectors available")
                return self._get_diverse_recent_articles(num_recommendations)
            
            user = self.user_preferences[user_id]
            
            # Handle new users with diverse recent articles
            if len(user.read_articles) == 0:
                logger.info("New user, returning diverse recent articles")
                return self._get_diverse_recent_articles(num_recommendations)
            
            # Calculate user profile from read articles
            read_vectors = []
            for aid in user.read_articles:
                if aid in self.articles and self.articles[aid].vector is not None:
                    vec = self.articles[aid].vector
                    if isinstance(vec, np.ndarray):
                        read_vectors.append(vec)
                    else:
                        try:
                            read_vectors.append(vec.toarray())
                        except:
                            continue
            
            if not read_vectors:
                logger.warning("No valid read vectors found")
                return self._get_diverse_recent_articles(num_recommendations)
            
            try:
                # Calculate user profile as mean of read article vectors
                read_vectors = np.vstack(read_vectors)
                user_profile = np.mean(read_vectors, axis=0)
                logger.info(f"User profile shape: {user_profile.shape}")
            except Exception as e:
                logger.error(f"Error calculating user profile: {str(e)}")
                return self._get_diverse_recent_articles(num_recommendations)
            
            # Calculate article scores considering multiple factors
            article_scores = []
            for article_id in self.article_ids:
                try:
                    if article_id in user.read_articles:
                        continue
                        
                    article = self.articles[article_id]
                    if article.vector is None:
                        continue
                    
                    # Convert article vector to numpy array
                    if isinstance(article.vector, np.ndarray):
                        article_vec = article.vector
                    else:
                        try:
                            article_vec = article.vector.toarray()
                        except:
                            continue
                    
                    # Ensure vectors have same shape
                    if article_vec.shape != user_profile.shape:
                        article_vec = article_vec.reshape(user_profile.shape)
                    
                    # Calculate cosine similarity with zero handling
                    norm_user = np.linalg.norm(user_profile)
                    norm_article = np.linalg.norm(article_vec)
                    
                    if norm_user == 0 or norm_article == 0:
                        similarity = 0.0
                    else:
                        similarity = float(np.dot(user_profile, article_vec) / (norm_user * norm_article))
                    
                    # Time decay factor
                    time_diff = (datetime.now(timezone.utc) - article.published_datetime).days
                    time_decay = np.exp(-0.1 * time_diff)
                    
                    # Category preference factor
                    category_weight = user.category_weights.get(article.category, 1.0)
                    
                    # Source diversity factor
                    source_factor = 1.0 / (self.source_diversity[article.source] ** 0.5)
                    
                    # Combined score
                    final_score = similarity * time_decay * category_weight * source_factor
                    article_scores.append((article_id, final_score))
                    
                except Exception as e:
                    logger.error(f"Error processing article {article_id}: {str(e)}")
                    continue
            
            if not article_scores:
                logger.warning("No article scores calculated")
                return self._get_diverse_recent_articles(num_recommendations)
            
            # Sort by score and ensure source diversity
            article_scores.sort(key=lambda x: x[1], reverse=True)
            recommended_articles = []
            seen_sources = set()
            
            for article_id, score in article_scores:
                if len(recommended_articles) >= num_recommendations:
                    break
                
                article = self.articles[article_id]
                if article.source not in seen_sources or len(seen_sources) >= num_recommendations // 2:
                    recommended_articles.append(article)
                    seen_sources.add(article.source)
            
            logger.info(f"Returning {len(recommended_articles)} recommendations")
            return recommended_articles
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return self._get_diverse_recent_articles(num_recommendations)
    
    def _get_diverse_recent_articles(self, num_articles: int) -> List[Article]:
        """Get recent articles from diverse sources"""
        try:
            # Convert datetime objects to timestamps for comparison
            articles_with_timestamps = [
                (article, article.published_datetime.timestamp())
                for article in self.articles.values()
            ]
            
            # Sort articles by timestamp
            recent_articles = sorted(
                articles_with_timestamps,
                key=lambda x: x[1],
                reverse=True
            )
            
            recommended = []
            seen_sources = set()
            
            for article, _ in recent_articles:
                if len(recommended) >= num_articles:
                    break
                    
                # Ensure source diversity
                if article.source not in seen_sources or len(seen_sources) >= num_articles // 2:
                    recommended.append(article)
                    seen_sources.add(article.source)
            
            return recommended
            
        except Exception as e:
            logger.error(f"Error getting diverse recent articles: {str(e)}")
            # Return first num_articles as fallback
            return list(self.articles.values())[:num_articles]
    