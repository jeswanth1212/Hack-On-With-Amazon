import pandas as pd
import numpy as np
import os
import logging
import sys
from pathlib import Path

# Add the project root to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.models.model import RecommendationEngine
from src.utils.context_utils import get_contextual_features

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/train_models.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define paths
PROCESSED_DIR = Path('data/processed')
MOVIES_PATH = PROCESSED_DIR / 'movies.csv'
USERS_PATH = PROCESSED_DIR / 'users.csv'
INTERACTIONS_PATH = PROCESSED_DIR / 'interactions.csv'

def load_data():
    """
    Load data from processed CSV files.
    
    Returns:
        tuple: (movies_df, users_df, interactions_df)
    """
    logger.info("Loading data...")
    
    # Check if the files exist
    if not (os.path.exists(MOVIES_PATH) and os.path.exists(USERS_PATH) and os.path.exists(INTERACTIONS_PATH)):
        logger.error("Processed data files not found. Run preprocess.py first.")
        return None, None, None
    
    # Load the data
    movies_df = pd.read_csv(MOVIES_PATH)
    users_df = pd.read_csv(USERS_PATH)
    interactions_df = pd.read_csv(INTERACTIONS_PATH)
    
    logger.info(f"Loaded {len(movies_df)} movies, {len(users_df)} users, and {len(interactions_df)} interactions")
    
    return movies_df, users_df, interactions_df

def prepare_context_features(interactions_df):
    """
    Prepare context features for the contextual adjustment model.
    
    Args:
        interactions_df (pandas.DataFrame): DataFrame with interactions
        
    Returns:
        tuple: (context_features, context_targets)
    """
    logger.info("Preparing context features...")
    
    # Extract context data and targets
    context_data_list = []
    context_targets = []
    
    for _, row in interactions_df.iterrows():
        # Create a context data dictionary
        context_data = {
            'mood': row['mood'],
            'time_of_day': row['time_of_day'],
            'day_of_week': row['day_of_week'],
            'weather': row['weather'],
            'age': None  # Will be filled from users_df
        }
        
        # Get context features
        context_features = get_contextual_features(context_data)
        context_data_list.append(context_features)
        
        # Add the sentiment score as the target
        context_targets.append(row['sentiment_score'])
    
    # Convert to numpy arrays
    context_features = np.array(context_data_list)
    context_targets = np.array(context_targets)
    
    logger.info(f"Prepared {len(context_features)} context features with {context_features.shape[1]} dimensions")
    
    return context_features, context_targets

def train_models(movies_df, users_df, interactions_df):
    """
    Train the recommendation models.
    
    Args:
        movies_df (pandas.DataFrame): DataFrame with movies
        users_df (pandas.DataFrame): DataFrame with users
        interactions_df (pandas.DataFrame): DataFrame with interactions
        
    Returns:
        RecommendationEngine: Trained recommendation engine
    """
    logger.info("Training recommendation models...")
    
    # Initialize the recommendation engine
    engine = RecommendationEngine(cf_weight=0.6, cb_weight=0.4)
    
    # Prepare context features
    context_features, context_targets = prepare_context_features(interactions_df)
    
    # Add a base score feature to the context features
    # In a real system, this would be the CF or hybrid score before contextual adjustment
    base_scores = np.random.uniform(0.5, 0.9, size=(len(context_features), 1))
    context_features_with_score = np.hstack([base_scores, context_features])
    
    # Train the models
    engine.train(
        interactions_df=interactions_df,
        items_df=movies_df,
        context_features=context_features_with_score,
        context_targets=context_targets
    )
    
    # Save the models
    engine.save_models()
    
    logger.info("Models trained and saved successfully")
    
    return engine

def test_recommendations(engine, users_df):
    """
    Test the recommendation engine by generating recommendations for a few users.
    
    Args:
        engine (RecommendationEngine): Trained recommendation engine
        users_df (pandas.DataFrame): DataFrame with users
    """
    logger.info("Testing recommendations...")
    
    # Get a few user IDs
    test_users = users_df['user_id'].tolist()[:3]
    
    for user_id in test_users:
        # Generate recommendations without context
        recommendations = engine.get_recommendations(user_id, n=5)
        
        # Log the recommendations
        logger.info(f"Top 5 recommendations for user {user_id} (without context):")
        for item_id, score in recommendations:
            logger.info(f"  - Item {item_id}: {score:.4f}")
        
        # Generate recommendations with context
        context_data = {
            'mood': 'happy',
            'time_of_day': 'evening',
            'day_of_week': 'Friday',
            'weather': 'clear',
            'age': 30
        }
        
        recommendations = engine.get_recommendations(user_id, n=5, context_data=context_data)
        
        # Log the recommendations
        logger.info(f"Top 5 recommendations for user {user_id} (with context - {context_data['mood']}, {context_data['time_of_day']}):")
        for item_id, score in recommendations:
            logger.info(f"  - Item {item_id}: {score:.4f}")

def main():
    """Main function to train the models."""
    logger.info("Starting model training...")
    
    # Load data
    movies_df, users_df, interactions_df = load_data()
    
    if movies_df is None or users_df is None or interactions_df is None:
        return
    
    # Train models
    engine = train_models(movies_df, users_df, interactions_df)
    
    # Test recommendations
    test_recommendations(engine, users_df)
    
    logger.info("Model training completed successfully")

if __name__ == "__main__":
    main() 