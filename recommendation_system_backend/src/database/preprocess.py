import pandas as pd
import numpy as np
import os
import gzip
import json
import logging
from pathlib import Path
import sys

# Add the project root to the path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.data.download import download_all_datasets, ensure_data_dirs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/preprocess.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define file paths
DATA_DIR = Path('data')
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

def create_directories():
    """Create necessary directories if they don't exist."""
    ensure_data_dirs()
    os.makedirs('logs', exist_ok=True)
    logger.info("Created necessary directories")

def process_movielens_data(movielens_dir, sample_size=None):
    """
    Process MovieLens dataset.
    
    Args:
        movielens_dir (Path): Path to MovieLens directory
        sample_size (int, optional): Number of rows to process
        
    Returns:
        tuple: (movies_df, ratings_df)
    """
    logger.info("Processing MovieLens dataset...")
    
    # Define paths
    movies_path = movielens_dir / "movies.csv"
    ratings_path = movielens_dir / "ratings.csv"
    
    # Load movies data
    try:
        movies_df = pd.read_csv(movies_path)
        logger.info(f"Loaded {len(movies_df)} movies from MovieLens")
        
        # Rename columns to match our schema
        movies_df = movies_df.rename(columns={
            'movieId': 'movielens_id',
            'title': 'title'
        })
        
        # Extract year from title
        movies_df['release_year'] = movies_df['title'].str.extract(r'\((\d{4})\)$')
        movies_df['title'] = movies_df['title'].str.replace(r'\s*\(\d{4}\)$', '', regex=True)
        
        # Generate a unique item_id
        movies_df['item_id'] = 'ml_' + movies_df['movielens_id'].astype(str)
        
        # Add additional columns required by our schema
        movies_df['title_type'] = 'movie'
        movies_df['runtime_minutes'] = np.nan
        movies_df['vote_average'] = np.nan
        movies_df['vote_count'] = np.nan
        movies_df['popularity'] = np.nan
        movies_df['is_trending'] = 0
        movies_df['overview'] = ''
        movies_df['imdb_id'] = ''
        movies_df['tmdb_id'] = ''
        
        # Apply sampling if specified
        if sample_size and sample_size < len(movies_df):
            movies_df = movies_df.sample(sample_size, random_state=42)
            logger.info(f"Sampled {len(movies_df)} movies")
    except Exception as e:
        logger.error(f"Error processing MovieLens movies: {e}")
        movies_df = pd.DataFrame()
    
    # Load ratings data
    try:
        ratings_df = pd.read_csv(ratings_path)
        logger.info(f"Loaded {len(ratings_df)} ratings from MovieLens")
        
        # Rename columns to match our schema
        ratings_df = ratings_df.rename(columns={
            'userId': 'user_id',
            'movieId': 'movielens_id',
            'rating': 'sentiment_score',
            'timestamp': 'unix_timestamp'
        })
        
        # Normalize sentiment score to 0-1 range (MovieLens ratings are 0.5-5)
        ratings_df['sentiment_score'] = ratings_df['sentiment_score'] / 5.0
        
        # Convert Unix timestamp to datetime
        ratings_df['timestamp'] = pd.to_datetime(ratings_df['unix_timestamp'], unit='s')
        
        # Add item_id to match with movies
        ratings_df['item_id'] = 'ml_' + ratings_df['movielens_id'].astype(str)
        
        # Drop the original movieId and unix_timestamp
        ratings_df = ratings_df.drop(columns=['movielens_id', 'unix_timestamp'])
        
        # Apply sampling if specified
        if sample_size and sample_size < len(ratings_df):
            ratings_df = ratings_df.sample(sample_size, random_state=42)
            logger.info(f"Sampled {len(ratings_df)} ratings")
    except Exception as e:
        logger.error(f"Error processing MovieLens ratings: {e}")
        ratings_df = pd.DataFrame()
    
    return movies_df, ratings_df

def process_tmdb_data(tmdb_dir, sample_size=None):
    """
    Process TMDB dataset.
    
    Args:
        tmdb_dir (Path): Path to TMDB directory
        sample_size (int, optional): Number of rows to process
        
    Returns:
        DataFrame: Movies from TMDB
    """
    logger.info("Processing TMDB dataset...")
    
    # Define paths
    movies_path = tmdb_dir / "tmdb_5000_movies.csv"
    credits_path = tmdb_dir / "tmdb_5000_credits.csv"
    
    # Load movies data
    try:
        tmdb_movies = pd.read_csv(movies_path)
        tmdb_credits = pd.read_csv(credits_path)
        
        logger.info(f"Loaded {len(tmdb_movies)} movies from TMDB")
        
        # Merge movies and credits
        tmdb_credits = tmdb_credits.rename(columns={'movie_id': 'id'})
        tmdb_data = pd.merge(tmdb_movies, tmdb_credits, on='id', how='inner')
        
        # Rename columns to match our schema
        tmdb_data = tmdb_data.rename(columns={
            'id': 'tmdb_id',
            'title_x': 'title',
            'vote_average': 'vote_average',
            'vote_count': 'vote_count',
            'popularity': 'popularity',
            'overview': 'overview',
            'release_date': 'release_date'
        })
        
        # Extract release year
        tmdb_data['release_year'] = pd.to_datetime(tmdb_data['release_date'], errors='coerce').dt.year
        
        # Clean up genres (stored as JSON string)
        def extract_genres(genres_json):
            try:
                genres = json.loads(genres_json)
                return ','.join([g['name'] for g in genres])
            except:
                return ''
        
        tmdb_data['genres'] = tmdb_data['genres'].apply(extract_genres)
        
        # Generate a unique item_id
        tmdb_data['item_id'] = 'tmdb_' + tmdb_data['tmdb_id'].astype(str)
        
        # Add additional columns required by our schema
        tmdb_data['title_type'] = 'movie'
        tmdb_data['runtime_minutes'] = tmdb_data['runtime']
        tmdb_data['is_trending'] = 0  # We'll update this later
        tmdb_data['imdb_id'] = ''
        tmdb_data['movielens_id'] = ''
        
        # Select required columns
        tmdb_data = tmdb_data[[
            'item_id', 'title', 'title_type', 'genres', 'release_year',
            'runtime_minutes', 'vote_average', 'vote_count', 'popularity',
            'is_trending', 'overview', 'imdb_id', 'tmdb_id', 'movielens_id'
        ]]
        
        # Mark trending movies (top 10% by popularity)
        popularity_threshold = tmdb_data['popularity'].quantile(0.9)
        tmdb_data.loc[tmdb_data['popularity'] >= popularity_threshold, 'is_trending'] = 1
        
        # Apply sampling if specified
        if sample_size and sample_size < len(tmdb_data):
            tmdb_data = tmdb_data.sample(sample_size, random_state=42)
            logger.info(f"Sampled {len(tmdb_data)} movies from TMDB")
    except Exception as e:
        logger.error(f"Error processing TMDB data: {e}")
        tmdb_data = pd.DataFrame()
    
    return tmdb_data

def create_users_from_ratings(ratings_df, sample_size=None):
    """
    Create a users dataframe from unique user IDs in ratings.
    
    Args:
        ratings_df (DataFrame): Ratings dataframe
        sample_size (int, optional): Number of users to include
        
    Returns:
        DataFrame: Users dataframe
    """
    logger.info("Creating users dataframe from ratings...")
    
    unique_user_ids = ratings_df['user_id'].unique()
    
    # Apply sampling if specified
    if sample_size and sample_size < len(unique_user_ids):
        unique_user_ids = np.random.choice(unique_user_ids, sample_size, replace=False)
        logger.info(f"Sampled {len(unique_user_ids)} users")
    
    # Create users dataframe
    users_df = pd.DataFrame({
        'user_id': unique_user_ids,
        'age': np.random.randint(18, 70, size=len(unique_user_ids)),
        'age_group': np.random.choice(['young_adult', 'adult', 'senior'], size=len(unique_user_ids)),
        'location': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston', 'London', 'Tokyo'], size=len(unique_user_ids))
    })
    
    logger.info(f"Created {len(users_df)} users")
    return users_df

def create_interactions_from_ratings(ratings_df, sample_size=None):
    """
    Create interactions dataframe from ratings.
    
    Args:
        ratings_df (DataFrame): Ratings dataframe
        sample_size (int, optional): Number of interactions to include
        
    Returns:
        DataFrame: Interactions dataframe
    """
    logger.info("Creating interactions dataframe from ratings...")
    
    # Apply sampling if specified
    if sample_size and sample_size < len(ratings_df):
        interactions_df = ratings_df.sample(sample_size, random_state=42)
    else:
        interactions_df = ratings_df.copy()
    
    # Add contextual features (randomly generated)
    interactions_df['mood'] = np.random.choice(['happy', 'sad', 'neutral', 'excited', 'relaxed'], size=len(interactions_df))
    interactions_df['time_of_day'] = np.random.choice(['morning', 'afternoon', 'evening', 'night'], size=len(interactions_df))
    interactions_df['day_of_week'] = np.random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], size=len(interactions_df))
    interactions_df['weather'] = np.random.choice(['sunny', 'cloudy', 'rainy', 'clear'], size=len(interactions_df))
    interactions_df['event_type'] = 'watch'
    
    logger.info(f"Created {len(interactions_df)} interactions")
    return interactions_df

def merge_movie_data(movielens_movies, tmdb_movies):
    """
    Merge movie data from different sources.
    
    Args:
        movielens_movies (DataFrame): MovieLens movies
        tmdb_movies (DataFrame): TMDB movies
        
    Returns:
        DataFrame: Merged movies dataframe
    """
    logger.info("Merging movie data from different sources...")
    
    # Check if both dataframes are not empty
    if not movielens_movies.empty and not tmdb_movies.empty:
        # Use all movies from both sources (no matching required for this demo)
        merged_movies = pd.concat([movielens_movies, tmdb_movies], ignore_index=True)
    elif not movielens_movies.empty:
        merged_movies = movielens_movies
    elif not tmdb_movies.empty:
        merged_movies = tmdb_movies
    else:
        logger.error("No movie data available from any source")
        return pd.DataFrame()
    
    logger.info(f"Merged movies dataframe contains {len(merged_movies)} movies")
    return merged_movies

def main(use_simulated_data=False, sample_size=None):
    """
    Main function to preprocess datasets.
    
    Args:
        use_simulated_data (bool): Whether to use simulated data (ignored, we're using real data)
        sample_size (int): Number of rows to process for each dataset
    """
    logger.info("Starting data preprocessing with real data...")
    
    # Create necessary directories
    create_directories()
    
    # Download datasets
    dataset_dirs = download_all_datasets()
    movielens_dir = dataset_dirs.get("movielens_dir")
    tmdb_dir = dataset_dirs.get("tmdb_dir")
    
    if not movielens_dir:
        logger.error("Failed to download MovieLens dataset")
        return
    
    # Process MovieLens data
    movielens_movies, ratings_df = process_movielens_data(movielens_dir, sample_size)
    
    # Process TMDB data if available
    tmdb_movies = pd.DataFrame()
    if tmdb_dir:
        tmdb_movies = process_tmdb_data(tmdb_dir, sample_size)
    
    # Merge movie data from different sources
    movies_df = merge_movie_data(movielens_movies, tmdb_movies)
    
    # Create users dataframe
    users_df = create_users_from_ratings(ratings_df, sample_size)
    
    # Create interactions dataframe
    interactions_df = create_interactions_from_ratings(ratings_df, sample_size)
    
    # Save processed data
    logger.info("Saving processed data...")
    movies_df.to_csv(PROCESSED_DIR / 'movies.csv', index=False)
    users_df.to_csv(PROCESSED_DIR / 'users.csv', index=False)
    interactions_df.to_csv(PROCESSED_DIR / 'interactions.csv', index=False)
    
    logger.info(f"Saved {len(movies_df)} movies, {len(users_df)} users, and {len(interactions_df)} interactions")
    logger.info("Data preprocessing completed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess datasets for the recommendation system')
    parser.add_argument('--sample', type=int, help='Number of rows to process for each dataset')
    
    args = parser.parse_args()
    
    # Always use real data
    main(False, args.sample) 