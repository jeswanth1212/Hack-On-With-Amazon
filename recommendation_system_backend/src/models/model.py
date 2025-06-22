import numpy as np
import pandas as pd
import os
import logging
import joblib
from pathlib import Path
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import SGDRegressor
import sys
import scipy.sparse as sp
import random

# Add the project root to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.context_utils import get_contextual_features

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
MODELS_DIR = Path('data/processed/models')
CF_MODEL_PATH = MODELS_DIR / 'cf_model.joblib'
TFIDF_MODEL_PATH = MODELS_DIR / 'tfidf_model.joblib'
CONTEXT_MODEL_PATH = MODELS_DIR / 'context_model.joblib'

class CollaborativeFilteringModel:
    """Collaborative filtering model using Singular Value Decomposition (SVD)."""
    
    def __init__(self, n_components=100, random_state=42):
        """
        Initialize the collaborative filtering model.
        
        Args:
            n_components (int): Number of components for SVD
            random_state (int): Random seed for reproducibility
        """
        self.n_components = n_components
        self.random_state = random_state
        self.model = TruncatedSVD(n_components=n_components, random_state=random_state)
        self.user_mapping = {}  # Maps user_id to row index
        self.item_mapping = {}  # Maps item_id to column index
        self.reverse_user_mapping = {}  # Maps row index to user_id
        self.reverse_item_mapping = {}  # Maps column index to item_id
        self.interaction_matrix = None
        self.user_factors = None
        self.item_factors = None
    
    def fit(self, interactions_df):
        """
        Fit the collaborative filtering model using user-item interactions.
        
        Args:
            interactions_df (pandas.DataFrame): DataFrame with user_id, item_id, sentiment_score
        """
        logger.info("Fitting collaborative filtering model...")
        
        # Create user and item mappings
        unique_users = interactions_df['user_id'].unique()
        unique_items = interactions_df['item_id'].unique()
        
        self.user_mapping = {user_id: i for i, user_id in enumerate(unique_users)}
        self.item_mapping = {item_id: i for i, item_id in enumerate(unique_items)}
        
        self.reverse_user_mapping = {i: user_id for user_id, i in self.user_mapping.items()}
        self.reverse_item_mapping = {i: item_id for item_id, i in self.item_mapping.items()}
        
        # Create the user-item interaction matrix
        n_users = len(unique_users)
        n_items = len(unique_items)
        self.interaction_matrix = np.zeros((n_users, n_items))
        
        # Fill the interaction matrix with sentiment scores
        for _, row in interactions_df.iterrows():
            user_idx = self.user_mapping.get(row['user_id'])
            item_idx = self.item_mapping.get(row['item_id'])
            
            if user_idx is not None and item_idx is not None:
                self.interaction_matrix[user_idx, item_idx] = row['sentiment_score']
        
        # Fit the SVD model
        self.user_factors = self.model.fit_transform(self.interaction_matrix)
        self.item_factors = self.model.components_.T
        
        logger.info(f"Collaborative filtering model trained with {n_users} users and {n_items} items")
    
    def predict(self, user_id, item_id):
        """
        Predict the rating for a user-item pair.
        
        Args:
            user_id (str): User ID
            item_id (str): Item ID
            
        Returns:
            float: Predicted rating (0-1 range)
        """
        user_idx = self.user_mapping.get(user_id)
        item_idx = self.item_mapping.get(item_id)
        
        if user_idx is None or item_idx is None:
            # If user or item is not in the training data, return a default score
            return 0.5
        
        # Get the user and item factors
        user_factor = self.user_factors[user_idx]
        item_factor = self.item_factors[item_idx]
        
        # Compute the dot product to get the predicted rating
        prediction = np.dot(user_factor, item_factor)
        
        # Clip the prediction to the 0-1 range
        return max(0.0, min(1.0, prediction))
    
    def get_user_recommendations(self, user_id, n=10, exclude_items=None):
        """
        Get top-N recommendations for a user.
        
        Args:
            user_id (str): User ID
            n (int): Number of recommendations to return
            exclude_items (list): List of item IDs to exclude from recommendations
            
        Returns:
            list: List of (item_id, predicted_rating) tuples
        """
        user_idx = self.user_mapping.get(user_id)
        
        if user_idx is None:
            # If user is not in the training data, return empty list
            return []
        
        # Get the user factors
        user_factor = self.user_factors[user_idx]
        
        # Compute predicted ratings for all items
        predicted_ratings = np.dot(user_factor, self.item_factors.T)
        
        # Create a list of (item_id, predicted_rating) tuples
        item_ratings = [(self.reverse_item_mapping[i], score) for i, score in enumerate(predicted_ratings)]
        
        # Exclude items if needed
        if exclude_items:
            item_ratings = [(item_id, score) for item_id, score in item_ratings if item_id not in exclude_items]
        
        # Sort by predicted rating (descending) and take the top N
        item_ratings.sort(key=lambda x: x[1], reverse=True)
        
        return item_ratings[:n]
    
    def save(self, path=CF_MODEL_PATH):
        """
        Save the model to disk.
        
        Args:
            path (Path): Path to save the model
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'n_components': self.n_components,
            'random_state': self.random_state,
            'user_mapping': self.user_mapping,
            'item_mapping': self.item_mapping,
            'reverse_user_mapping': self.reverse_user_mapping,
            'reverse_item_mapping': self.reverse_item_mapping,
            'interaction_matrix': self.interaction_matrix,
            'user_factors': self.user_factors,
            'item_factors': self.item_factors
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Saved collaborative filtering model to {path}")
    
    def load(self, path=CF_MODEL_PATH):
        """
        Load the model from disk.
        
        Args:
            path (Path): Path to load the model from
            
        Returns:
            bool: True if the model was loaded successfully, False otherwise
        """
        try:
            model_data = joblib.load(path)
            
            self.n_components = model_data['n_components']
            self.random_state = model_data['random_state']
            self.user_mapping = model_data['user_mapping']
            self.item_mapping = model_data['item_mapping']
            self.reverse_user_mapping = model_data['reverse_user_mapping']
            self.reverse_item_mapping = model_data['reverse_item_mapping']
            self.interaction_matrix = model_data['interaction_matrix']
            self.user_factors = model_data['user_factors']
            self.item_factors = model_data['item_factors']
            
            # Recreate the SVD model
            self.model = TruncatedSVD(n_components=self.n_components, random_state=self.random_state)
            
            logger.info(f"Loaded collaborative filtering model from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading collaborative filtering model from {path}: {e}")
            return False


class ContentBasedFilteringModel:
    """Content-based filtering model using TF-IDF and cosine similarity."""
    
    def __init__(self):
        """Initialize the content-based filtering model."""
        self.tfidf_vectorizer = TfidfVectorizer(
            analyzer='word',
            stop_words='english',
            max_features=5000,
            ngram_range=(1, 2)
        )
        self.item_features = None
        self.item_ids = None
        self.similarity_matrix = None
    
    def fit(self, items_df):
        """
        Fit the content-based filtering model using item metadata.
        
        Args:
            items_df (pandas.DataFrame): DataFrame with item metadata
        """
        logger.info("Fitting content-based filtering model...")
        
        # Combine genres and overview for better content representation
        items_df['content'] = items_df['genres'].fillna('') + ' ' + items_df['overview'].fillna('')
        
        # Store the item IDs
        self.item_ids = items_df['item_id'].tolist()
        
        # Fit the TF-IDF vectorizer and transform the content
        self.item_features = self.tfidf_vectorizer.fit_transform(items_df['content'])
        
        # Compute the similarity matrix
        self.similarity_matrix = cosine_similarity(self.item_features)
        
        logger.info(f"Content-based filtering model trained with {len(self.item_ids)} items")
    
    def get_similar_items(self, item_id, n=10, exclude_items=None):
        """
        Get top-N similar items for a given item.
        
        Args:
            item_id (str): Item ID
            n (int): Number of similar items to return
            exclude_items (list): List of item IDs to exclude
            
        Returns:
            list: List of (item_id, similarity_score) tuples
        """
        try:
            # Find the index of the item
            item_idx = self.item_ids.index(item_id)
        except ValueError:
            # If the item is not in the training data, return empty list
            return []
        
        # Get the similarity scores for the item
        similarity_scores = self.similarity_matrix[item_idx]
        
        # Create a list of (item_id, similarity_score) tuples
        similar_items = [(self.item_ids[i], score) for i, score in enumerate(similarity_scores)]
        
        # Exclude the item itself and any other items if needed
        similar_items = [(item, score) for item, score in similar_items if item != item_id]
        if exclude_items:
            similar_items = [(item, score) for item, score in similar_items if item not in exclude_items]
        
        # Sort by similarity score (descending) and take the top N
        similar_items.sort(key=lambda x: x[1], reverse=True)
        
        return similar_items[:n]
    
    def save(self, path=TFIDF_MODEL_PATH):
        """
        Save the model to disk.
        
        Args:
            path (Path): Path to save the model
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'item_features': self.item_features,
            'item_ids': self.item_ids,
            'similarity_matrix': self.similarity_matrix
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Saved content-based filtering model to {path}")
    
    def load(self, path=TFIDF_MODEL_PATH):
        """
        Load the model from disk.
        
        Args:
            path (Path): Path to load the model from
            
        Returns:
            bool: True if the model was loaded successfully, False otherwise
        """
        try:
            model_data = joblib.load(path)
            
            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.item_features = model_data['item_features']
            self.item_ids = model_data['item_ids']
            self.similarity_matrix = model_data['similarity_matrix']
            
            logger.info(f"Loaded content-based filtering model from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading content-based filtering model from {path}: {e}")
            return False


class ContextualAdjustmentModel:
    """Contextual adjustment model using SGDRegressor for online learning."""
    
    def __init__(self, random_state=42):
        """
        Initialize the contextual adjustment model.
        
        Args:
            random_state (int): Random seed for reproducibility
        """
        self.model = SGDRegressor(
            loss='squared_error',
            penalty='l2',
            alpha=0.0001,
            l1_ratio=0.15,
            max_iter=1000,
            tol=1e-3,
            shuffle=True,
            random_state=random_state,
            learning_rate='adaptive',
            eta0=0.01
        )
        self.feature_names = None
    
    def fit(self, X, y):
        """
        Fit the contextual adjustment model.
        
        Args:
            X (numpy.ndarray): Feature matrix
            y (numpy.ndarray): Target values
        """
        logger.info("Fitting contextual adjustment model...")
        
        # Fit the model
        self.model.fit(X, y)
        
        logger.info(f"Contextual adjustment model trained with {X.shape[0]} samples and {X.shape[1]} features")
    
    def predict(self, X):
        """
        Predict the contextual adjustment.
        
        Args:
            X (numpy.ndarray): Feature matrix
            
        Returns:
            numpy.ndarray: Predicted contextual adjustments
        """
        # Predict the contextual adjustment
        predictions = self.model.predict(X)
        
        # Clip the predictions to the 0-1 range
        predictions = np.clip(predictions, 0, 1)
        
        return predictions
    
    def partial_fit(self, X, y):
        """
        Update the model with new data (online learning).
        
        Args:
            X (numpy.ndarray): Feature matrix
            y (numpy.ndarray): Target values
        """
        # Update the model with new data
        self.model.partial_fit(X, y)
    
    def save(self, path=CONTEXT_MODEL_PATH):
        """
        Save the model to disk.
        
        Args:
            path (Path): Path to save the model
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Saved contextual adjustment model to {path}")
    
    def load(self, path=CONTEXT_MODEL_PATH):
        """
        Load the model from disk.
        
        Args:
            path (Path): Path to load the model from
            
        Returns:
            bool: True if the model was loaded successfully, False otherwise
        """
        try:
            model_data = joblib.load(path)
            
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            
            logger.info(f"Loaded contextual adjustment model from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading contextual adjustment model from {path}: {e}")
            return False


class RecommendationEngine:
    """
    Recommendation engine combining collaborative filtering, content-based filtering,
    and contextual adjustments to provide personalized recommendations.
    """
    
    def __init__(self, cf_weight=0.6, cb_weight=0.4, context_alpha=0.5):
        """
        Initialize the recommendation engine.
        
        Args:
            cf_weight (float): Weight of collaborative filtering in hybrid recommendations
            cb_weight (float): Weight of content-based filtering in hybrid recommendations
            context_alpha (float): Weight of contextual adjustment
        """
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        self.context_alpha = context_alpha
        
        # Create models directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        # Initialize model components
        self.user_item_matrix = None
        self.item_features = None
        self.svd_model = None
        self.tfidf_vectorizer = None
        self.context_model = None
        self.items_df = None
        self.item_ids = None
        self.user_ids = None
        self.item_id_to_idx = {}
        self.user_id_to_idx = {}
        self.user_factors = None
        self.item_factors = None
        
        # Load pre-trained models if they exist
        self._load_models()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def _load_models(self):
        """Load pre-trained models if they exist."""
        try:
            # Load collaborative filtering model
            if os.path.exists(MODELS_DIR / 'svd_model.joblib'):
                self.svd_model = joblib.load(MODELS_DIR / 'svd_model.joblib')
                logger.info("Loaded SVD model")
            
            # Load content-based model
            if os.path.exists(MODELS_DIR / 'tfidf_vectorizer.joblib'):
                self.tfidf_vectorizer = joblib.load(MODELS_DIR / 'tfidf_vectorizer.joblib')
                logger.info("Loaded TF-IDF vectorizer")
            
            # Load context model
            if os.path.exists(MODELS_DIR / 'context_model.joblib'):
                self.context_model = joblib.load(MODELS_DIR / 'context_model.joblib')
                logger.info("Loaded context model")
            
            # Load item features
            if os.path.exists(MODELS_DIR / 'item_features.joblib'):
                self.item_features = joblib.load(MODELS_DIR / 'item_features.joblib')
                logger.info("Loaded item features")
            
            # Load user and item mappings
            if os.path.exists(MODELS_DIR / 'item_id_to_idx.joblib'):
                self.item_id_to_idx = joblib.load(MODELS_DIR / 'item_id_to_idx.joblib')
                logger.info("Loaded item ID to index mapping")
            
            if os.path.exists(MODELS_DIR / 'user_id_to_idx.joblib'):
                self.user_id_to_idx = joblib.load(MODELS_DIR / 'user_id_to_idx.joblib')
                logger.info("Loaded user ID to index mapping")
            
            # Load items dataframe
            if os.path.exists(MODELS_DIR / 'items_df.joblib'):
                self.items_df = joblib.load(MODELS_DIR / 'items_df.joblib')
                logger.info("Loaded items dataframe")
            
            # Load user and item factors
            if os.path.exists(MODELS_DIR / 'user_factors.joblib'):
                self.user_factors = joblib.load(MODELS_DIR / 'user_factors.joblib')
                logger.info("Loaded user factors")
            
            if os.path.exists(MODELS_DIR / 'item_factors.joblib'):
                self.item_factors = joblib.load(MODELS_DIR / 'item_factors.joblib')
                logger.info("Loaded item factors")
            
            # Load user-item matrix
            if os.path.exists(MODELS_DIR / 'user_item_matrix.joblib'):
                self.user_item_matrix = joblib.load(MODELS_DIR / 'user_item_matrix.joblib')
                logger.info("Loaded user-item matrix")
            
            # Get user and item IDs
            if self.user_id_to_idx:
                self.user_ids = list(self.user_id_to_idx.keys())
                logger.info(f"Loaded {len(self.user_ids)} user IDs")
            
            if self.item_id_to_idx:
                self.item_ids = list(self.item_id_to_idx.keys())
                logger.info(f"Loaded {len(self.item_ids)} item IDs")
        
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
            logger.info("Will train new models")
    
    def save_models(self):
        """Save trained models to disk."""
        try:
            # Save collaborative filtering model
            if self.svd_model is not None:
                joblib.dump(self.svd_model, MODELS_DIR / 'svd_model.joblib')
            
            # Save content-based model
            if self.tfidf_vectorizer is not None:
                joblib.dump(self.tfidf_vectorizer, MODELS_DIR / 'tfidf_vectorizer.joblib')
            
            # Save context model
            if self.context_model is not None:
                joblib.dump(self.context_model, MODELS_DIR / 'context_model.joblib')
            
            # Save item features
            if self.item_features is not None:
                joblib.dump(self.item_features, MODELS_DIR / 'item_features.joblib')
            
            # Save user and item mappings
            if self.item_id_to_idx:
                joblib.dump(self.item_id_to_idx, MODELS_DIR / 'item_id_to_idx.joblib')
            
            if self.user_id_to_idx:
                joblib.dump(self.user_id_to_idx, MODELS_DIR / 'user_id_to_idx.joblib')
            
            # Save items dataframe
            if self.items_df is not None:
                joblib.dump(self.items_df, MODELS_DIR / 'items_df.joblib')
            
            # Save user and item factors
            if self.user_factors is not None:
                joblib.dump(self.user_factors, MODELS_DIR / 'user_factors.joblib')
            
            if self.item_factors is not None:
                joblib.dump(self.item_factors, MODELS_DIR / 'item_factors.joblib')
            
            # Save user-item matrix
            if self.user_item_matrix is not None:
                joblib.dump(self.user_item_matrix, MODELS_DIR / 'user_item_matrix.joblib')
            
            logger.info("Saved all models to disk")
        
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _prepare_user_item_matrix(self, interactions_df):
        """
        Prepare the user-item matrix from interactions.
        
        Args:
            interactions_df (pandas.DataFrame): DataFrame with interactions
            
        Returns:
            scipy.sparse.csr_matrix: Sparse user-item matrix
        """
        logger.info("Preparing user-item matrix...")
        
        # Create user and item ID mappings
        self.user_ids = interactions_df['user_id'].unique()
        self.item_ids = interactions_df['item_id'].unique()
        
        self.user_id_to_idx = {user_id: i for i, user_id in enumerate(self.user_ids)}
        self.item_id_to_idx = {item_id: i for i, item_id in enumerate(self.item_ids)}
        
        # Create user-item matrix
        user_item_matrix = np.zeros((len(self.user_ids), len(self.item_ids)))
        
        for _, row in interactions_df.iterrows():
            user_idx = self.user_id_to_idx.get(row['user_id'])
            item_idx = self.item_id_to_idx.get(row['item_id'])
            
            if user_idx is not None and item_idx is not None:
                user_item_matrix[user_idx, item_idx] = row['sentiment_score']
        
        self.user_item_matrix = user_item_matrix
        
        logger.info(f"Created user-item matrix with shape {user_item_matrix.shape}")
        
        return user_item_matrix
    
    def _train_collaborative_filtering(self, user_item_matrix):
        """
        Train collaborative filtering model using SVD.
        
        Args:
            user_item_matrix (numpy.ndarray): User-item matrix
        """
        logger.info("Training collaborative filtering model...")
        
        # Get dimensions
        n_users, n_items = user_item_matrix.shape
        
        # Determine number of components
        n_components = min(50, min(n_users, n_items) - 1)
        
        # Initialize SVD model
        self.svd_model = TruncatedSVD(n_components=n_components, random_state=42)
        
        # Fit SVD model
        self.item_factors = self.svd_model.fit_transform(user_item_matrix.T)
        self.user_factors = self.svd_model.components_.T
        
        logger.info(f"Trained SVD model with {n_components} components")
    
    def _train_content_based(self, items_df):
        """
        Train content-based filtering model using TF-IDF.
        
        Args:
            items_df (pandas.DataFrame): DataFrame with items
        """
        logger.info("Training content-based filtering model...")
        
        # Store items dataframe
        self.items_df = items_df
        
        # Prepare item text data (combining title, genres, and overview)
        items_df['text'] = items_df['title'] + ' ' + items_df['genres'].fillna('') + ' ' + items_df['overview'].fillna('')
        
        # Initialize TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        
        # Fit TF-IDF vectorizer and transform item text
        self.item_features = self.tfidf_vectorizer.fit_transform(items_df['text'])
        
        logger.info(f"Trained TF-IDF vectorizer with {self.item_features.shape[1]} features")
    
    def _train_context_model(self, context_features, context_targets):
        """
        Train context model for adjusting recommendations based on context.
        
        Args:
            context_features (numpy.ndarray): Context features
            context_targets (numpy.ndarray): Context targets (sentiment scores)
        """
        logger.info("Training context model...")
        
        # Initialize context model
        self.context_model = SGDRegressor(random_state=42)
        
        # Fit context model
        self.context_model.fit(context_features, context_targets)
        
        logger.info("Trained context model")
    
    def train(self, interactions_df, items_df, context_features=None, context_targets=None):
        """
        Train all components of the recommendation engine.
        
        Args:
            interactions_df (pandas.DataFrame): DataFrame with interactions
            items_df (pandas.DataFrame): DataFrame with items
            context_features (numpy.ndarray, optional): Context features
            context_targets (numpy.ndarray, optional): Context targets
        """
        logger.info("Training recommendation engine...")
        
        # Prepare user-item matrix
        user_item_matrix = self._prepare_user_item_matrix(interactions_df)
        
        # Train collaborative filtering model
        self._train_collaborative_filtering(user_item_matrix)
        
        # Train content-based filtering model
        self._train_content_based(items_df)
        
        # Train context model if context data is provided
        if context_features is not None and context_targets is not None:
            self._train_context_model(context_features, context_targets)
        
        logger.info("Recommendation engine training complete")
    
    def _get_cf_recommendations(self, user_id, n=10, exclude_items=None):
        """
        Get collaborative filtering recommendations for a user.
        
        Args:
            user_id (str): User ID
            n (int): Number of recommendations
            exclude_items (list, optional): List of item IDs to exclude
            
        Returns:
            list: List of (item_id, score) tuples
        """
        # Check if models are trained
        if self.user_factors is None or self.item_factors is None:
            logger.warning("Collaborative filtering models not trained")
            return []
        
        # Get user index
        user_idx = self.user_id_to_idx.get(user_id)
        
        # Handle new users
        if user_idx is None:
            logger.warning(f"User {user_id} not found in training data")
            # Return random items for new users
            if self.item_ids is not None and len(self.item_ids) > 0:
                items_to_recommend = np.random.choice(self.item_ids, min(n, len(self.item_ids)), replace=False)
                return [(item_id, 0.5) for item_id in items_to_recommend]
            else:
                return []
        
        # Get user vector
        user_vector = self.user_factors[user_idx]
        
        # Compute scores for all items
        scores = np.dot(self.item_factors, user_vector)
        
        # Create item ID and score pairs
        item_scores = list(zip(self.item_ids, scores))
        
        # Filter out excluded items
        if exclude_items:
            item_scores = [(item_id, score) for item_id, score in item_scores if item_id not in exclude_items]
        
        # Sort by score and take top N
        item_scores.sort(key=lambda x: x[1], reverse=True)
        
        return item_scores[:n]
    
    def _get_cb_recommendations(self, user_id, n=10, exclude_items=None):
        """
        Get content-based recommendations for a user based on their interaction history.
        
        Args:
            user_id (str): User ID
            n (int): Number of recommendations
            exclude_items (list, optional): List of item IDs to exclude
            
        Returns:
            list: List of (item_id, score) tuples
        """
        # Check if models are trained
        if self.item_features is None or self.user_item_matrix is None:
            logger.warning("Content-based filtering models not trained")
            return []
        
        # Get user index
        user_idx = self.user_id_to_idx.get(user_id)
        
        # Handle new users
        if user_idx is None:
            logger.warning(f"User {user_id} not found in training data")
            # Return trending items for new users
            if self.items_df is not None and 'is_trending' in self.items_df.columns:
                trending_items = self.items_df[self.items_df['is_trending'] == 1]['item_id'].tolist()
                if trending_items:
                    return [(item_id, 0.5) for item_id in trending_items[:n]]
            
            # If no trending items, return random items
            if self.item_ids is not None and len(self.item_ids) > 0:
                items_to_recommend = np.random.choice(self.item_ids, min(n, len(self.item_ids)), replace=False)
                return [(item_id, 0.5) for item_id in items_to_recommend]
            else:
                return []
        
        # Get user's interaction history
        user_items = self.user_item_matrix[user_idx]
        
        # Find items the user has interacted with
        interacted_indices = np.where(user_items > 0)[0]
        
        if len(interacted_indices) == 0:
            logger.warning(f"User {user_id} has no interactions")
            # Return trending items for users with no interactions
            if self.items_df is not None and 'is_trending' in self.items_df.columns:
                trending_items = self.items_df[self.items_df['is_trending'] == 1]['item_id'].tolist()
                if trending_items:
                    return [(item_id, 0.5) for item_id in trending_items[:n]]
            return []
        
        # Get features of items the user has interacted with
        user_item_features = self.item_features[interacted_indices]
        
        # Weight features by interaction scores
        user_item_scores = user_items[interacted_indices]
        
        # Create weighted average of features
        if sp.issparse(user_item_features):
            user_profile = user_item_features.multiply(user_item_scores[:, np.newaxis])
            user_profile = user_profile.mean(axis=0)
            # Convert to array to avoid numpy matrix issues
            if isinstance(user_profile, np.matrix):
                user_profile = np.asarray(user_profile)
        else:
            # For dense arrays
            user_profile = np.average(user_item_features, axis=0, weights=user_item_scores)
            user_profile = user_profile.reshape(1, -1)
        
        # Compute similarity between user profile and all items
        scores = cosine_similarity(user_profile, self.item_features).flatten()
        
        # Create item ID and score pairs
        item_scores = list(zip(self.item_ids, scores))
        
        # Filter out items the user has already interacted with
        interacted_items = [self.item_ids[idx] for idx in interacted_indices]
        item_scores = [(item_id, score) for item_id, score in item_scores if item_id not in interacted_items]
        
        # Filter out excluded items
        if exclude_items:
            item_scores = [(item_id, score) for item_id, score in item_scores if item_id not in exclude_items]
        
        # Sort by score and take top N
        item_scores.sort(key=lambda x: x[1], reverse=True)
        
        return item_scores[:n]
    
    def _apply_context_adjustment(self, recommendations, context_data):
        """
        Apply contextual adjustment to recommendations.
        
        Args:
            recommendations (list): List of (item_id, score) tuples
            context_data (dict): Contextual data
            
        Returns:
            list: List of (item_id, adjusted_score) tuples
        """
        # Check if context model is trained
        if self.context_model is None:
            logger.warning("Context model not trained, using manual context adjustment")
            return self._manual_context_adjustment(recommendations, context_data)
        
        # Get context features
        context_features = get_contextual_features(context_data)
        
        # Adjust scores based on context
        adjusted_recommendations = []
        
        for item_id, score in recommendations:
            # Create feature vector with base score and context features
            features = np.hstack([[score], context_features])
            
            # Predict adjusted score
            try:
                adjusted_score = self.context_model.predict([features])[0]
                
                # Apply stronger influence of context (amplify the difference)
                context_effect = (adjusted_score - score) * (1 + self.context_alpha)
                adjusted_score = score + context_effect
                
                # Ensure score is in 0-1 range
                adjusted_score = max(0, min(1, adjusted_score))
                
                adjusted_recommendations.append((item_id, adjusted_score))
            except Exception as e:
                logger.error(f"Error in context model prediction: {e}")
                adjusted_recommendations.append((item_id, score))
        
        # Sort by adjusted score
        adjusted_recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return adjusted_recommendations
        
    def _manual_context_adjustment(self, recommendations, context_data):
        """
        Apply manual context-based adjustments when context model is not available.
        
        Args:
            recommendations (list): List of (item_id, score) tuples
            context_data (dict): Contextual data
            
        Returns:
            list: List of (item_id, adjusted_score) tuples
        """
        adjusted_recommendations = []
        
        # Get item genres if items_df is available
        item_genres = {}
        if self.items_df is not None and 'item_id' in self.items_df.columns and 'genres' in self.items_df.columns:
            for _, row in self.items_df.iterrows():
                item_genres[row['item_id']] = row['genres'] if pd.notna(row['genres']) else ''
        
        mood = context_data.get('mood')
        time_of_day = context_data.get('time_of_day')
        day_of_week = context_data.get('day_of_week')
        weather = context_data.get('weather')
        age = context_data.get('age')
        
        for item_id, score in recommendations:
            adjustment = 0
            
            # Get genre for this item
            genre = item_genres.get(item_id, '')
            
            # Apply mood-based adjustments
            if mood == 'happy':
                if 'Comedy' in genre or 'Adventure' in genre:
                    adjustment += 0.15
                if 'Drama' in genre or 'Horror' in genre:
                    adjustment -= 0.1
            elif mood == 'sad':
                if 'Drama' in genre or 'Romance' in genre:
                    adjustment += 0.15
                if 'Comedy' in genre or 'Action' in genre:
                    adjustment -= 0.05
            
            # Apply time-based adjustments
            if time_of_day == 'evening' or time_of_day == 'night':
                if 'Horror' in genre or 'Thriller' in genre:
                    adjustment += 0.1
            elif time_of_day == 'morning':
                if 'Documentary' in genre or 'Family' in genre:
                    adjustment += 0.1
            
            # Apply day-based adjustments
            if day_of_week in ['Friday', 'Saturday']:
                if 'Action' in genre or 'Adventure' in genre:
                    adjustment += 0.1
            elif day_of_week in ['Sunday', 'Monday']:
                if 'Documentary' in genre or 'Drama' in genre:
                    adjustment += 0.05
            
            # Apply weather-based adjustments
            if weather == 'rainy' or weather == 'snowy':
                if 'Drama' in genre or 'Romance' in genre:
                    adjustment += 0.1
            elif weather == 'sunny' or weather == 'clear':
                if 'Adventure' in genre or 'Action' in genre:
                    adjustment += 0.1
            
            # Apply age-based adjustments
            if age is not None:
                if age < 13:  # Kids
                    if 'Family' in genre or 'Animation' in genre:
                        adjustment += 0.2
                    if 'Horror' in genre or 'Thriller' in genre:
                        adjustment -= 0.3
                elif age < 18:  # Teens
                    if 'Adventure' in genre or 'Sci-Fi' in genre:
                        adjustment += 0.15
                elif age < 30:  # Young adults
                    if 'Action' in genre or 'Comedy' in genre:
                        adjustment += 0.1
                elif age < 50:  # Adults
                    if 'Drama' in genre or 'Thriller' in genre:
                        adjustment += 0.1
                else:  # Seniors
                    if 'Documentary' in genre or 'Drama' in genre:
                        adjustment += 0.1
            
            # Apply adjustment
            adjusted_score = min(1.0, max(0.0, score + adjustment))
            adjusted_recommendations.append((item_id, adjusted_score))
        
        # Sort by adjusted score
        adjusted_recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return adjusted_recommendations
    
    def _get_content_based_recommendations(self, user_id, n=10, context_data=None, exclude_items=None):
        """
        Get content-based recommendations for new or cold-start users.
        Uses contextual data to personalize results.
        
        Args:
            user_id: User ID
            n: Number of recommendations
            context_data: Contextual data
            exclude_items: Items to exclude
        
        Returns:
            List of (item_id, score) tuples
        """
        self.logger.warning(f"User {user_id} not found in training data")
        
        if exclude_items is None:
            exclude_items = []
            
        # Get popular items as a fallback
        popular_items = []
        
        try:
            # Use database to get popular items
            from src.database.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get items with more than 5 interactions, sorted by popularity
            cursor.execute('''
                SELECT item_id, COUNT(*) as interaction_count 
                FROM interactions 
                GROUP BY item_id 
                HAVING COUNT(*) > 5 
                ORDER BY interaction_count DESC 
                LIMIT 100
            ''')
            
            items = cursor.fetchall()
            conn.close()
            
            # Convert to item_id list
            if items:
                popular_items = [item['item_id'] for item in items]
        except Exception as e:
            self.logger.error(f"Error getting popular items: {e}")
        
        # If database query didn't work, use item popularity from model
        if not popular_items and hasattr(self, 'item_popularity'):
            popular_items = [item_id for item_id, _ in 
                            sorted(self.item_popularity.items(), key=lambda x: x[1], reverse=True)[:100]]
        
        # If still no popular items, use a fallback method
        if not popular_items:
            # Create a simple fallback list of recommendations if all else fails
            if hasattr(self, 'item_ids') and len(self.item_ids) > 0:
                import random
                # Use a subset of all known items
                all_items = list(self.item_ids)
                random.shuffle(all_items)
                popular_items = all_items[:min(100, len(all_items))]
            else:
                # If we have no items at all, return an empty list
                self.logger.error("No items available for recommendations")
                return []
        
        # Filter out excluded items
        popular_items = [item_id for item_id in popular_items if item_id not in exclude_items]
        
        # Apply contextual adjustments if available
        if context_data and popular_items:
            # Get item metadata
            item_metadata = {}
            
            try:
                # Get item details from database
                conn = get_db_connection()
                cursor = conn.cursor()
                
                placeholders = ','.join(['?' for _ in popular_items])
                cursor.execute(f"SELECT * FROM items WHERE item_id IN ({placeholders})", popular_items)
                items = cursor.fetchall()
                conn.close()
                
                for item in items:
                    item_metadata[item['item_id']] = {
                        'genres': item.get('genres', ''),
                        'language': item.get('language', ''),
                        'release_year': item.get('release_year'),
                    }
            except Exception as e:
                self.logger.error(f"Error getting item metadata: {e}")
            
            # Score items based on context
            item_scores = {}
            
            for item_id in popular_items:
                base_score = 0.5  # Start with moderate score
                
                # Add random noise to create variation (0.1 range)
                import random
                base_score += (random.random() * 0.2) - 0.1
                
                # Adjust based on item metadata if available
                metadata = item_metadata.get(item_id, {})
                
                # Mood-based adjustments
                if context_data.get('mood') and metadata.get('genres'):
                    genres = str(metadata['genres']).lower()
                    mood = str(context_data['mood']).lower()
                    
                    # Happy/excited: boost comedy, action, adventure
                    if mood in ['happy', 'excited']:
                        if any(g in genres for g in ['comedy', 'action', 'adventure', 'animation']):
                            base_score += 0.15
                    
                    # Sad: boost drama, romance
                    elif mood in ['sad', 'depressed']:
                        if any(g in genres for g in ['drama', 'romance']):
                            base_score += 0.15
                    
                    # Relaxed: boost documentary, drama
                    elif mood in ['relaxed', 'calm']:
                        if any(g in genres for g in ['documentary', 'drama']):
                            base_score += 0.15
                
                # Time-based adjustments
                if context_data.get('time_of_day') and metadata.get('genres'):
                    genres = str(metadata['genres']).lower()
                    time = str(context_data['time_of_day']).lower()
                    
                    # Evening/night: boost thriller, horror
                    if time in ['evening', 'night']:
                        if any(g in genres for g in ['thriller', 'horror', 'mystery']):
                            base_score += 0.1
                    
                    # Morning: boost comedy, animation
                    elif time in ['morning']:
                        if any(g in genres for g in ['comedy', 'animation', 'family']):
                            base_score += 0.1
                
                # Language preference adjustments
                if context_data.get('language') and metadata.get('language'):
                    if context_data['language'] == metadata.get('language'):
                        base_score += 0.2
                
                item_scores[item_id] = base_score
            
            # Convert to list, sort by score
            recommendations = [(item_id, score) for item_id, score in item_scores.items()]
            recommendations.sort(key=lambda x: x[1], reverse=True)
            
            # Add randomness for cold-start users to ensure diversity
            import random
            if len(recommendations) > n*2:
                # Take top 30% deterministically
                top_items = recommendations[:int(n*0.3)]
                # Randomly select from the rest
                remaining = recommendations[int(n*0.3):n*3]
                random.shuffle(remaining)
                random_items = remaining[:n-len(top_items)]
                recommendations = top_items + random_items
                recommendations.sort(key=lambda x: x[1], reverse=True)
            
            return recommendations[:n]
        
        # If no context or metadata, return random selection of popular items
        import random
        random.shuffle(popular_items)
        return [(item_id, 0.5) for item_id in popular_items[:n]]

    def _apply_contextual_adjustments(self, scores, context_data):
        """
        Apply contextual adjustments to recommendation scores.
        
        Args:
            scores: Dictionary of item_id -> score
            context_data: Contextual data
            
        Returns:
            Updated scores dictionary
        """
        if not context_data:
            return scores
            
        # Create a copy to avoid modifying the original
        adjusted_scores = scores.copy()
        
        try:
            # Load item metadata if available
            item_metadata = {}
            item_ids = list(scores.keys())
            
            if not item_ids:
                return scores
                
            try:
                # Get item details from database
                from src.database.database import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Get metadata for all items in batches
                batch_size = 100
                all_items = []
                
                for i in range(0, len(item_ids), batch_size):
                    batch_ids = item_ids[i:i+batch_size]
                    placeholders = ','.join(['?' for _ in batch_ids])
                    cursor.execute(f"SELECT * FROM items WHERE item_id IN ({placeholders})", batch_ids)
                    batch_items = cursor.fetchall()
                    all_items.extend(batch_items)
                
                conn.close()
                
                for item in all_items:
                    item_metadata[item['item_id']] = {
                        'genres': item.get('genres', ''),
                        'language': item.get('language', ''),
                        'release_year': item.get('release_year'),
                    }
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error getting item metadata for contextual adjustment: {e}")
                else:
                    logging.error(f"Error getting item metadata for contextual adjustment: {e}")
            
            # Apply adjustments based on available context
            for item_id, score in adjusted_scores.items():
                metadata = item_metadata.get(item_id, {})
                adjustment = 0.0
                
                # Mood-based adjustments
                if context_data.get('mood') and metadata.get('genres'):
                    genres = str(metadata.get('genres', '')).lower()
                    mood = str(context_data['mood']).lower()
                    
                    # Define genre preferences for each mood
                    mood_genre_map = {
                        'happy': ['comedy', 'animation', 'adventure', 'family'],
                        'sad': ['drama', 'romance'],
                        'excited': ['action', 'adventure', 'sci-fi'],
                        'relaxed': ['documentary', 'drama', 'family'],
                        'bored': ['thriller', 'mystery', 'action'],
                        'stressed': ['comedy', 'animation', 'family'],
                        'curious': ['documentary', 'mystery', 'sci-fi'],
                        'neutral': [],  # No specific preference
                    }
                    
                    # Check if any preferred genres match
                    preferred_genres = mood_genre_map.get(mood, [])
                    for genre in preferred_genres:
                        if genre in genres:
                            adjustment += 0.08  # Cumulative adjustment for multiple matches
                            break
                
                # Time-based adjustments
                if context_data.get('time_of_day') and metadata.get('genres'):
                    genres = str(metadata.get('genres', '')).lower()
                    time = str(context_data['time_of_day']).lower()
                    
                    # Define genre preferences for each time
                    time_genre_map = {
                        'morning': ['comedy', 'animation', 'family', 'documentary'],
                        'afternoon': ['action', 'adventure', 'comedy'],
                        'evening': ['drama', 'thriller', 'romance'],
                        'night': ['horror', 'thriller', 'mystery', 'sci-fi'],
                    }
                    
                    # Check if any preferred genres match
                    preferred_genres = time_genre_map.get(time, [])
                    for genre in preferred_genres:
                        if genre in genres:
                            adjustment += 0.06
                            break
                
                # Weather-based adjustments
                if context_data.get('weather') and metadata.get('genres'):
                    genres = str(metadata.get('genres', '')).lower()
                    weather = str(context_data['weather']).lower()
                    
                    # Define genre preferences for each weather
                    weather_genre_map = {
                        'sunny': ['comedy', 'adventure', 'action'],
                        'rainy': ['drama', 'thriller', 'romance'],
                        'cloudy': ['drama', 'mystery', 'thriller'],
                        'snowy': ['family', 'drama', 'romance'],
                        'stormy': ['horror', 'thriller', 'mystery'],
                        'windy': ['action', 'adventure', 'comedy'],
                        'foggy': ['horror', 'mystery', 'thriller'],
                        'clear': ['sci-fi', 'adventure', 'action'],
                    }
                    
                    # Check if any preferred genres match
                    preferred_genres = weather_genre_map.get(weather, [])
                    for genre in preferred_genres:
                        if genre in genres:
                            adjustment += 0.05
                            break
                
                # Language preference adjustments - increased weight
                if context_data.get('language') and metadata.get('language'):
                    if context_data['language'] == metadata.get('language'):
                        adjustment += 0.35  # Significantly increased from 0.15
                    
                # Age-based adjustments - strengthen them
                if context_data.get('age') and metadata.get('genres'):
                    genres = str(metadata.get('genres', '')).lower()
                    age = context_data.get('age')
                    
                    if age is not None:
                        if age < 13:  # Kids
                            if any(g in genres for g in ['family', 'animation', 'children']):
                                adjustment += 0.3
                            if any(g in genres for g in ['horror', 'thriller', 'violent']):
                                adjustment -= 0.4  # Stronger negative adjustment
                        elif age < 18:  # Teens
                            if any(g in genres for g in ['adventure', 'sci-fi']):
                                adjustment += 0.25
                        elif age < 30:  # Young adults
                            if any(g in genres for g in ['action', 'comedy']):
                                adjustment += 0.2
                        elif age < 50:  # Adults
                            if any(g in genres for g in ['drama', 'thriller']):
                                adjustment += 0.2
                        else:  # Seniors
                            if any(g in genres for g in ['documentary', 'drama', 'history']):
                                adjustment += 0.25
                
                # Location-based adjustments
                if context_data.get('location') and metadata.get('genres'):
                    genres = str(metadata.get('genres', '')).lower()
                    location = str(context_data.get('location', '')).lower()
                    
                    # Different content for different locations
                    if 'india' in location:
                        if 'bollywood' in genres:
                            adjustment += 0.3
                    elif 'japan' in location:
                        if any(g in genres for g in ['anime', 'japanese']):
                            adjustment += 0.3
                    elif 'korea' in location:
                        if 'korean' in genres:
                            adjustment += 0.3
                            
                # Check for user's preferred genres
                if context_data.get('preferred_genres') and metadata.get('genres'):
                    genres = str(metadata.get('genres', '')).lower()
                    preferred_genres = context_data.get('preferred_genres', [])
                    
                    for genre in preferred_genres:
                        if genre.lower() in genres:
                            adjustment += 0.25
                            break
                
                # Apply the total adjustment
                adjusted_scores[item_id] = min(1.0, max(0.1, score + adjustment))
            
            # Add small random variations to create diversity between users
            import random
            for item_id in adjusted_scores:
                random_factor = (random.random() * 0.1) - 0.05  # -0.05 to +0.05
                adjusted_scores[item_id] = min(1.0, max(0.1, adjusted_scores[item_id] + random_factor))
            
            return adjusted_scores
            
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error applying contextual adjustments: {e}")
            else:
                logging.error(f"Error applying contextual adjustments: {e}")
            return scores  # Return original scores on error
    
    def get_recommendations(self, user_id, n=10, context_data=None, exclude_items=None):
        """
        Get personalized recommendations for a user with optional context.
        
        Args:
            user_id: User ID
            n: Number of recommendations to return
            context_data: Contextual data (mood, time, etc.)
            exclude_items: Items to exclude
            
        Returns:
            List of (item_id, score) tuples
        """
        # Log request
        self.logger.info(f"Getting recommendations for user {user_id}")
        
        if exclude_items is None:
            exclude_items = []
        
        # Get user index
        user_idx = self.user_id_to_idx.get(user_id)
        
        # If user not found, use content-based recommendations
        if user_idx is None:
            self.logger.warning(f"User {user_id} not found in training data")
            return self._get_content_based_recommendations(user_id, n, context_data, exclude_items)
        
        try:
            # Get basic user preferences - recent items, interactions, etc.
            user_vectors = self._get_user_vectors(user_idx, user_id)
            
            # Add randomness to user vectors to ensure variation between different recommendation calls
            import numpy as np
            import random
            
            # Apply small noise to the user vector (0.05 standard deviation)
            if hasattr(user_vectors, 'toarray'):
                user_vector_array = user_vectors.toarray()
                random_noise = np.random.normal(0, 0.05, user_vector_array.shape)
                user_vector_array = user_vector_array + random_noise
                user_vectors = np.array(user_vector_array)
            elif isinstance(user_vectors, np.ndarray):
                # If it's already a NumPy array, add noise directly
                random_noise = np.random.normal(0, 0.05, user_vectors.shape)
                user_vectors = user_vectors + random_noise
            
            # Calculate similarity scores
            scores = {}
            
            # Get predicted scores from matrix factorization (SVD)
            if hasattr(self, 'svd_user_factors') and hasattr(self, 'svd_item_factors') and self.svd_user_factors is not None and self.svd_item_factors is not None:
                preds = self._get_mf_predictions(user_idx)
                for item_id, score in preds:
                    if exclude_items and item_id in exclude_items:
                        continue
                    scores[item_id] = score
            else:
                # Fallback if MF model not available
                self.logger.warning("Matrix factorization models not available, using fallback")
                # Fall back to content-based recommendations
                return self._get_content_based_recommendations(user_id, n, context_data, exclude_items)
            
            # Apply contextual adjustments
            if context_data:
                scores = self._apply_contextual_adjustments(scores, context_data)
            
            # Sort by score and return top n
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            # Add randomness to ensure different results each time
            # Take more candidates than needed and randomly select from them
            top_candidates = sorted_scores[:min(n*3, len(sorted_scores))]
            
            if len(top_candidates) > n:
                # Select top n/3 items deterministically
                top_n_fixed = top_candidates[:n//3]
                
                # Select the rest randomly from remaining candidates
                remaining = top_candidates[n//3:]
                random.shuffle(remaining)
                random_selection = remaining[:n - len(top_n_fixed)]
                
                # Combine and sort again
                final_selection = top_n_fixed + random_selection
                final_selection.sort(key=lambda x: x[1], reverse=True)
                
                return final_selection
            
            return top_candidates[:n]
            
        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            self.logger.warning(f"Falling back to content-based recommendations for user {user_id}")
            return self._get_content_based_recommendations(user_id, n, context_data, exclude_items)
    
    def record_interaction(self, user_id, item_id, sentiment_score, context_data=None):
        """
        Record a user-item interaction for online updates.
        
        Updates the user-item matrix and factors to reflect the new interaction.
        
        Args:
            user_id (str): User ID
            item_id (str): Item ID
            sentiment_score (float): Sentiment score (0-1)
            context_data (dict, optional): Contextual data
        """
        logger.info(f"Recording interaction: user={user_id}, item={item_id}, score={sentiment_score}")
        
        # Add user if not already in the system
        if user_id not in self.user_id_to_idx:
            new_user_idx = len(self.user_ids)
            self.user_ids = np.append(self.user_ids, user_id)
            self.user_id_to_idx[user_id] = new_user_idx
            
            # Expand user_item_matrix
            if self.user_item_matrix is not None:
                new_row = np.zeros((1, self.user_item_matrix.shape[1]))
                self.user_item_matrix = np.vstack([self.user_item_matrix, new_row])
            
            # Expand user_factors if they exist
            if self.user_factors is not None:
                if len(self.user_factors) > 0:
                    # Average of existing user factors as initial value
                    new_user_factor = np.mean(self.user_factors, axis=0).reshape(1, -1)
                    self.user_factors = np.vstack([self.user_factors, new_user_factor])
                else:
                    # If no user factors exist yet, initialize with zeros
                    n_components = self.item_factors.shape[1] if self.item_factors is not None else 50
                    self.user_factors = np.zeros((1, n_components))
        
        # Add item if not already in the system
        if item_id not in self.item_id_to_idx:
            new_item_idx = len(self.item_ids)
            self.item_ids = np.append(self.item_ids, item_id)
            self.item_id_to_idx[item_id] = new_item_idx
            
            # Expand user_item_matrix
            if self.user_item_matrix is not None:
                new_col = np.zeros((self.user_item_matrix.shape[0], 1))
                self.user_item_matrix = np.hstack([self.user_item_matrix, new_col])
            
            # Expand item_factors if they exist
            if self.item_factors is not None:
                if len(self.item_factors) > 0:
                    # Average of existing item factors as initial value
                    new_item_factor = np.mean(self.item_factors, axis=0).reshape(1, -1)
                    self.item_factors = np.vstack([self.item_factors, new_item_factor])
                else:
                    # If no item factors exist yet, initialize with zeros
                    n_components = self.user_factors.shape[1] if self.user_factors is not None else 50
                    self.item_factors = np.zeros((1, n_components))
        
        # Get indices
        user_idx = self.user_id_to_idx[user_id]
        item_idx = self.item_id_to_idx[item_id]
        
        # Update user-item matrix
        if self.user_item_matrix is not None:
            self.user_item_matrix[user_idx, item_idx] = sentiment_score
        
        # Perform incremental update to factors (simplified for real-time)
        if self.user_factors is not None and self.item_factors is not None:
            # Get current factors
            user_factor = self.user_factors[user_idx]
            item_factor = self.item_factors[item_idx]
            
            # Calculate the error between prediction and actual
            predicted = np.dot(user_factor, item_factor)
            error = sentiment_score - predicted
            
            # Gradient descent update (learning rate = 0.01)
            lr = 0.01
            user_update = lr * error * item_factor
            item_update = lr * error * user_factor
            
            # Update the factors
            self.user_factors[user_idx] += user_update
            self.item_factors[item_idx] += item_update
            
            logger.info(f"Updated user and item factors for user {user_id} and item {item_id}")
        
        # If context model exists, we could update it too using the context_data
        if context_data and self.context_model is not None:
            try:
                context_features = get_contextual_features(context_data)
                # Create feature vector with predicted score and context features
                predicted_score = np.dot(self.user_factors[user_idx], self.item_factors[item_idx].T)
                features = np.hstack([[predicted_score], context_features])
                
                # Update context model
                self.context_model.partial_fit([features], [sentiment_score])
                logger.info(f"Updated context model with new interaction data")
            except Exception as e:
                logger.error(f"Error updating context model: {e}")

    def load_models(self):
        """Public method to load pre-trained models. Returns True if successful, False otherwise."""
        try:
            self._load_models()
            return True
        except Exception as e:
            logger.error(f"Error in load_models: {e}")
            return False

    def _get_user_vectors(self, user_idx, user_id):
        """
        Get user vectors for recommendations.
        
        Args:
            user_idx: User index
            user_id: User ID
            
        Returns:
            User vector for recommendations
        """
        try:
            # Get user interactions
            if self.user_item_matrix is not None and user_idx < self.user_item_matrix.shape[0]:
                user_vector = self.user_item_matrix[user_idx]
                return user_vector
            
            # Fallback to user factors if available
            if hasattr(self, 'svd_user_factors') and self.svd_user_factors is not None:
                if user_idx < len(self.svd_user_factors) and len(self.svd_user_factors) > 0:
                    return self.svd_user_factors[user_idx]
            
            # If no user vector available, return empty
            return np.zeros(self.item_content_matrix.shape[1]) if self.item_content_matrix is not None else None
            
        except Exception as e:
            self.logger.error(f"Error getting user vectors: {e}")
            return None

    def _get_mf_predictions(self, user_idx):
        """
        Get predictions using matrix factorization (SVD).
        
        Args:
            user_idx: User index
            
        Returns:
            List of (item_id, score) tuples
        """
        try:
            import numpy as np
            
            if not hasattr(self, 'svd_user_factors') or not hasattr(self, 'svd_item_factors'):
                self.logger.warning("Matrix factorization models not available")
                return []
                
            if self.svd_user_factors is None or self.svd_item_factors is None:
                self.logger.warning("Matrix factorization factors are None")
                return []
                
            if user_idx >= len(self.svd_user_factors):
                self.logger.warning(f"User index {user_idx} out of bounds for SVD model")
                return []
            
            # Get user factors
            user_factors = self.svd_user_factors[user_idx]
            
            # Calculate predictions
            predictions = []
            
            # For each item, calculate the predicted rating
            for item_idx in range(len(self.svd_item_factors)):
                item_factors = self.svd_item_factors[item_idx]
                
                # Calculate predicted rating
                predicted_rating = np.dot(user_factors, item_factors)
                
                # Map item index back to item ID
                if item_idx in self.idx_to_item_id:
                    item_id = self.idx_to_item_id[item_idx]
                    predictions.append((item_id, float(predicted_rating)))
            
            # Sort by predicted rating (descending)
            predictions.sort(key=lambda x: x[1], reverse=True)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error in _get_mf_predictions: {e}")
            return []