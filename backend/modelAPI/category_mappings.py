from typing import Dict, List, Optional
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import defaultdict
import json
import os
from datetime import datetime, timedelta
import pickle
import joblib

# Main categories that match the model's classification labels
MAIN_CATEGORIES = {
    0: "tech",
    1: "business",
    2: "politics",
    3: "entertainment",
    4: "sport"
}

# Keyword mappings for subcategory detection
SUBCATEGORY_KEYWORDS = {
    # Tech subcategories
    "artificial_intelligence": ["ai", "artificial intelligence", "machine learning", "ml", "neural network", "deep learning", "chatgpt", "gpt", "llm", "large language model"],
    "computing": ["computer", "computing", "processor", "cpu", "gpu", "hardware", "software", "programming", "code", "developer"],
    "software": ["software", "app", "application", "program", "developer", "coding", "programming", "api", "sdk", "framework"],
    "hardware": ["hardware", "device", "computer", "processor", "cpu", "gpu", "motherboard", "circuit", "chip", "semiconductor"],
    "internet": ["internet", "web", "online", "website", "browser", "network", "cloud", "server", "hosting", "domain"],
    "mobile": ["mobile", "smartphone", "android", "ios", "iphone", "app", "mobile app", "mobile device", "tablet"],
    "gaming": ["game", "gaming", "console", "playstation", "xbox", "nintendo", "esports", "gamer", "video game"],
    "cybersecurity": ["security", "cyber", "hack", "hacker", "malware", "virus", "firewall", "encryption", "privacy", "breach"],
    "robotics": ["robot", "robotics", "automation", "automated", "mechanical", "machine", "industrial robot"],
    "startups": ["startup", "venture", "funding", "investor", "founder", "entrepreneur", "seed", "series a", "unicorn"],
    
    # Business subcategories
    "finance": ["finance", "financial", "bank", "banking", "investment", "stock", "market", "trading", "fund", "money"],
    "markets": ["market", "stock", "trading", "investor", "share", "price", "index", "exchange", "trading", "bull", "bear"],
    "economy": ["economy", "economic", "gdp", "inflation", "recession", "growth", "fiscal", "monetary", "policy"],
    "investing": ["invest", "investment", "investor", "portfolio", "asset", "fund", "stock", "bond", "equity"],
    "companies": ["company", "corporation", "business", "enterprise", "firm", "startup", "merger", "acquisition"],
    "trade": ["trade", "trading", "export", "import", "tariff", "commerce", "business", "market", "exchange"],
    "employment": ["job", "employment", "hire", "recruit", "career", "workforce", "labor", "salary", "wage"],
    "real_estate": ["real estate", "property", "housing", "mortgage", "rent", "landlord", "tenant", "home", "apartment"],
    "cryptocurrency": ["crypto", "bitcoin", "ethereum", "blockchain", "token", "coin", "wallet", "mining", "defi", "nft"],
    "energy": ["energy", "power", "electricity", "renewable", "solar", "wind", "nuclear", "oil", "gas", "fuel"],
    
    # Politics subcategories
    "government": ["government", "administration", "policy", "minister", "official", "bureaucracy", "public sector"],
    "elections": ["election", "vote", "campaign", "candidate", "poll", "ballot", "voter", "democrat", "republican"],
    "policy": ["policy", "legislation", "law", "regulation", "bill", "act", "statute", "reform", "initiative"],
    "international": ["international", "foreign", "diplomacy", "treaty", "alliance", "global", "world", "nation"],
    "diplomacy": ["diplomacy", "diplomatic", "embassy", "consulate", "ambassador", "foreign relations", "treaty"],
    "legislation": ["legislation", "law", "bill", "act", "statute", "regulation", "congress", "parliament", "senate"],
    "political_parties": ["party", "democrat", "republican", "liberal", "conservative", "political party", "faction"],
    "public_affairs": ["public", "affairs", "policy", "government", "administration", "public sector", "civil service"],
    "security": ["security", "defense", "military", "intelligence", "terrorism", "threat", "protection", "safety"],
    "immigration": ["immigration", "immigrant", "migration", "refugee", "asylum", "border", "citizenship", "visa"],
    
    # Entertainment subcategories
    "movies": ["movie", "film", "cinema", "actor", "actress", "director", "box office", "premiere", "theater"],
    "music": ["music", "song", "album", "artist", "band", "concert", "tour", "performance", "musician", "singer"],
    "television": ["tv", "television", "show", "series", "episode", "broadcast", "channel", "network", "streaming"],
    "celebrity": ["celebrity", "star", "famous", "actor", "actress", "singer", "artist", "personality", "influencer"],
    "arts": ["art", "artist", "exhibition", "gallery", "museum", "painting", "sculpture", "creative", "design"],
    "gaming": ["game", "gaming", "console", "playstation", "xbox", "nintendo", "esports", "gamer", "video game"],
    "theater": ["theater", "theatre", "play", "drama", "performance", "stage", "broadway", "musical", "acting"],
    "fashion": ["fashion", "style", "clothing", "designer", "model", "runway", "trend", "apparel", "wear"],
    "books": ["book", "author", "novel", "publisher", "literature", "writing", "reading", "bestseller", "fiction"],
    "streaming": ["streaming", "netflix", "hulu", "disney+", "amazon prime", "platform", "content", "series"],
    
    # Sport subcategories
    "football": ["football", "soccer", "premier league", "champions league", "world cup", "player", "team", "match", "goal"],
    "basketball": ["basketball", "nba", "player", "team", "game", "court", "hoop", "dunk", "shoot", "basket"],
    "tennis": ["tennis", "grand slam", "wimbledon", "player", "match", "tournament", "serve", "court", "racket"],
    "golf": ["golf", "tournament", "player", "course", "club", "hole", "green", "fairway", "putt", "swing"],
    "olympics": ["olympic", "games", "athlete", "medal", "competition", "sport", "olympics", "paralympics"],
    "cricket": ["cricket", "bat", "ball", "wicket", "bowler", "batsman", "match", "test", "odi", "t20"],
    "rugby": ["rugby", "match", "team", "player", "tackle", "try", "scrum", "league", "union", "tournament"],
    "athletics": ["athletics", "track", "field", "race", "running", "jumping", "throwing", "sprint", "marathon"],
    "soccer": ["soccer", "football", "match", "team", "player", "goal", "league", "championship", "tournament"],
    "baseball": ["baseball", "mlb", "game", "team", "player", "pitch", "bat", "ball", "home run", "stadium"],
    "mma": ["mma", "ufc", "mixed martial arts", "octagon", "fighter", "weight class", "championship", "belt", "knockout", "submission", "dana white", "bellator", "one championship"]
}

# Subcategory mappings to main categories
SUBCATEGORY_MAPPINGS = {
    # Tech subcategories
    "Artificial Intelligence": "tech",
    "Computing": "tech",
    "software": "tech",
    "hardware": "tech",
    "internet": "tech",
    "mobile": "tech",
    "gaming": "tech",
    "cybersecurity": "tech",
    "robotics": "tech",
    "startups": "tech",
    
    # Business subcategories
    "finance": "business",
    "markets": "business",
    "economy": "business",
    "investing": "business",
    "companies": "business",
    "trade": "business",
    "employment": "business",
    "real_estate": "business",
    "cryptocurrency": "business",
    "energy": "business",
    
    # Politics subcategories
    "government": "politics",
    "elections": "politics",
    "policy": "politics",
    "international": "politics",
    "diplomacy": "politics",
    "legislation": "politics",
    "political_parties": "politics",
    "public_affairs": "politics",
    "security": "politics",
    "immigration": "politics",
    
    # Entertainment subcategories
    "movies": "entertainment",
    "music": "entertainment",
    "television": "entertainment",
    "celebrity": "entertainment",
    "arts": "entertainment",
    "gaming": "entertainment",
    "theater": "entertainment",
    "fashion": "entertainment",
    "books": "entertainment",
    "streaming": "entertainment",
    
    # Sport subcategories
    "football": "sport",
    "basketball": "sport",
    "tennis": "sport",
    "golf": "sport",
    "olympics": "sport",
    "cricket": "sport",
    "rugby": "sport",
    "athletics": "sport",
    "soccer": "sport",
    "baseball": "sport",
    "mma": "sport"
}

# Training data for each subcategory (example articles/sentences)
SUBCATEGORY_TRAINING_DATA = {
    # Tech subcategories
    "artificial intelligence": [
        "OpenAI's GPT-4 demonstrates remarkable capabilities in natural language understanding",
        "Machine learning algorithms are revolutionizing data analysis",
        "Neural networks are becoming increasingly sophisticated",
        "Deep learning models are achieving unprecedented accuracy",
        "AI systems are transforming various industries"
    ],
    "computing": [
        "New processor architecture promises significant performance improvements",
        "Quantum computing research shows promising results",
        "Cloud computing services are expanding rapidly",
        "Edge computing is becoming more prevalent",
        "High-performance computing enables complex simulations"
    ],
    # Sport subcategories
    "mma": [
        "UFC champion defends title in spectacular knockout victory",
        "Mixed martial arts fighter makes successful debut in the octagon",
        "MMA event draws record-breaking pay-per-view numbers",
        "Fighter moves up weight class for championship bout",
        "UFC announces new fight card with multiple title matches"
    ],
    # ... Add more training data for other subcategories ...
}

class TrainingDataCollector:
    def __init__(self, data_dir: str = "training_data"):
        self.data_dir = data_dir
        self.training_data_file = os.path.join(data_dir, "subcategory_training_data.json")
        self._ensure_data_dir()
        self.training_data = self._load_training_data()

    def _ensure_data_dir(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_training_data(self) -> Dict[str, List[str]]:
        """Load existing training data from file."""
        if os.path.exists(self.training_data_file):
            with open(self.training_data_file, 'r') as f:
                return json.load(f)
        return defaultdict(list)

    def save_training_data(self):
        """Save training data to file."""
        with open(self.training_data_file, 'w') as f:
            json.dump(self.training_data, f, indent=2)

    def add_article(self, text: str, subcategory: str):
        """Add a new article to the training data."""
        if subcategory in SUBCATEGORY_MAPPINGS:
            # Clean and prepare the text
            cleaned_text = self._clean_text(text)
            if cleaned_text:
                self.training_data[subcategory].append(cleaned_text)
                self.save_training_data()

    def _clean_text(self, text: str) -> str:
        """Clean and prepare text for training."""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def get_training_data(self) -> Dict[str, List[str]]:
        """Get the current training data."""
        return self.training_data

# Initialize the data collector
training_collector = TrainingDataCollector()

# Update the SubcategoryClassifier to use the collected data
class SubcategoryClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        self.category_vectors = {}
        self.model_dir = "models"
        self._ensure_model_dir()
        self._load_or_train()

    def _ensure_model_dir(self):
        """Create model directory if it doesn't exist."""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def _get_model_paths(self):
        """Get paths for saved model components."""
        return {
            'vectorizer': os.path.join(self.model_dir, 'vectorizer.joblib'),
            'category_vectors': os.path.join(self.model_dir, 'category_vectors.joblib'),
            'metadata': os.path.join(self.model_dir, 'model_metadata.json')
        }

    def save_model(self):
        """Save the trained model components to disk."""
        paths = self._get_model_paths()
        
        # Save vectorizer
        joblib.dump(self.vectorizer, paths['vectorizer'])
        
        # Save category vectors
        joblib.dump(self.category_vectors, paths['category_vectors'])
        
        # Save metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'num_categories': len(self.category_vectors),
            'categories': list(self.category_vectors.keys())
        }
        with open(paths['metadata'], 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved successfully at {self.model_dir}")

    def load_model(self) -> bool:
        """Load the trained model components from disk."""
        paths = self._get_model_paths()
        
        try:
            # Check if all required files exist
            if not all(os.path.exists(path) for path in paths.values()):
                return False
            
            # Load vectorizer
            self.vectorizer = joblib.load(paths['vectorizer'])
            
            # Load category vectors
            self.category_vectors = joblib.load(paths['category_vectors'])
            
            # Load and print metadata
            with open(paths['metadata'], 'r') as f:
                metadata = json.load(f)
                # print(f"Loaded model from {metadata['timestamp']}")
                # print(f"Number of categories: {metadata['num_categories']}")
                # print(f"Categories: {', '.join(metadata['categories'])}")
            
            return True
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False

    def _load_or_train(self):
        """Load existing model or train a new one."""
        if not self.load_model():
            print("No saved model found or error loading model. Training new model...")
            self._train_classifier()
            self.save_model()

    def _train_classifier(self):
        """Train the classifier using the collected training data."""
        # Get training data from collector
        training_data = training_collector.get_training_data()
        
        # Prepare all training texts
        all_texts = []
        category_labels = []
        
        for category, texts in training_data.items():
            all_texts.extend(texts)
            category_labels.extend([category] * len(texts))
        
        if not all_texts:
            # Fall back to example data if no training data available
            all_texts = []
            category_labels = []
            for category, texts in SUBCATEGORY_TRAINING_DATA.items():
                all_texts.extend(texts)
                category_labels.extend([category] * len(texts))
        
        # Fit and transform the vectorizer
        self.vectorizer.fit(all_texts)
        
        # Create category vectors
        for category in set(category_labels):
            category_texts = [text for text, label in zip(all_texts, category_labels) if label == category]
            if category_texts:
                category_vectors = self.vectorizer.transform(category_texts)
                self.category_vectors[category] = category_vectors.mean(axis=0)

    def predict_subcategory(self, text: str, main_category: str) -> Optional[str]:
        """
        Predict the most likely subcategory for a given text within a main category.
        Uses TF-IDF and cosine similarity to find the best match.
        """
        # Get relevant subcategories for the main category
        subcategories = get_subcategories(main_category)
        if not subcategories:
            return None

        # Transform the input text
        text_vector = self.vectorizer.transform([text])
        
        # Calculate similarities with each category
        similarities = {}
        for subcategory in subcategories:
            if subcategory in self.category_vectors:
                # Handle both sparse matrices and numpy matrices
                if hasattr(text_vector, 'toarray'):
                    text_array = text_vector.toarray()
                else:
                    text_array = np.asarray(text_vector)
                    
                if hasattr(self.category_vectors[subcategory], 'toarray'):
                    category_array = self.category_vectors[subcategory].toarray()
                else:
                    category_array = np.asarray(self.category_vectors[subcategory])
                
                similarity = cosine_similarity(text_array, category_array)[0][0]
                similarities[subcategory] = similarity
        
        # Return the subcategory with highest similarity if it exceeds threshold
        if similarities:
            best_subcategory = max(similarities.items(), key=lambda x: x[1])
            if best_subcategory[1] > 0.2:  # Similarity threshold
                return best_subcategory[0]
        
        return None

    def retrain(self):
        """Retrain the model with current training data and save it."""
        self._train_classifier()
        self.save_model()

# Initialize the classifier
subcategory_classifier = SubcategoryClassifier()

def detect_subcategory(text: str, main_category: str) -> Optional[str]:
    """
    Detect the most likely subcategory based on NLP analysis of the text.
    Uses the trained SubcategoryClassifier to make predictions.
    """
    return subcategory_classifier.predict_subcategory(text, main_category)

def get_main_category(category: str) -> str:
    """
    Maps a category (either main or subcategory) to its main category.
    If the input is already a main category, returns it unchanged.
    If the input is a subcategory, returns the corresponding main category.
    If the input is not found, returns 'other'.
    """
    # Check if it's a main category
    if category in MAIN_CATEGORIES.values():
        return category
    
    # Check if it's a subcategory
    if category in SUBCATEGORY_MAPPINGS:
        return SUBCATEGORY_MAPPINGS[category]
    
    # If not found, return 'other'
    return "other"

def get_subcategories(main_category: str) -> List[str]:
    """
    Returns a list of subcategories for a given main category.
    Returns empty list if the main category doesn't exist or has no subcategories.
    """
    return [
        subcat for subcat, main_cat in SUBCATEGORY_MAPPINGS.items()
        if main_cat == main_category
    ]

def is_valid_category(category: str) -> bool:
    """
    Checks if a category is either a main category or a subcategory.
    """
    return (
        category in MAIN_CATEGORIES.values() or
        category in SUBCATEGORY_MAPPINGS
    )

def validate_category(category: str) -> bool:
    """
    Validates if a given category is a valid main category.
    """
    return category in MAIN_CATEGORIES.values()

def validate_subcategory(subcategory: str) -> bool:
    """
    Validates if a given subcategory is valid.
    """
    return subcategory in SUBCATEGORY_MAPPINGS

def map_to_main_category(category: str) -> str:
    """
    Maps any category (main or sub) to its main category.
    """
    return get_main_category(category)

def map_to_subcategory(category: str, text: str = "") -> Optional[str]:
    """
    Returns a subcategory for a given category based on text analysis.
    If text is provided, uses NLP analysis to determine the most appropriate subcategory.
    If no text is provided or no matches are found, returns the first subcategory for the category.
    """
    if category in SUBCATEGORY_MAPPINGS:
        return category
        
    if text:
        detected_subcategory = detect_subcategory(text, category)
        if detected_subcategory:
            return detected_subcategory
            
    subcats = get_subcategories(category)
    return subcats[0] if subcats else None