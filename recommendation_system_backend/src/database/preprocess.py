import os
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path

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

# Define data directories
DATA_DIR = Path('data')
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

# Define language mappings for user preferences
LANGUAGE_PREFERENCES = {
    'hi': 'Hindi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam',
    'kn': 'Kannada',
    'bn': 'Bengali',
    'mr': 'Marathi',
    'pa': 'Punjabi',
    'gu': 'Gujarati',
    'or': 'Odia',
    'as': 'Assamese',
    'en': 'English',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German'
}

# Map ISO language codes to regions for local recommendations
LANGUAGE_TO_REGION = {
    'hi': 'India',
    'ta': 'India',
    'te': 'India',
    'ml': 'India',
    'kn': 'India',
    'bn': 'India',
    'mr': 'India',
    'pa': 'India',
    'gu': 'India',
    'or': 'India',
    'as': 'India',
    'en': 'International',
    'ja': 'Japan',
    'ko': 'Korea',
    'zh': 'China',
    'fr': 'France',
    'es': 'Spain',
    'de': 'Germany'
}

def create_directories():
    """Create necessary directories if they don't exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Created necessary directories")

def process_movielens_dataset():
    """Process MovieLens dataset (not used in new implementation)."""
    logger.info("MovieLens dataset will not be used in the new system.")
    return None, None

def process_tmdb_dataset(tmdb_dir):
    """
    Process TMDB dataset.
    
    Args:
        tmdb_dir: Directory containing TMDB dataset
        
    Returns:
        tuple: (items_df, None)
    """
    logger.info("Processing TMDB dataset...")
    
    # Check if TMDB JSON file exists
    tmdb_file = tmdb_dir / 'tmdb_movies.json'
    
    if not tmdb_file.exists():
        logger.error(f"TMDB file not found: {tmdb_file}")
        return None, None
    
    try:
        with open(tmdb_file, 'r', encoding='utf-8') as f:
            tmdb_movies = json.load(f)
        
        logger.info(f"Loaded {len(tmdb_movies)} movies from TMDB JSON")
        
        # Process TMDB movies
        tmdb_data = []
        
        for movie in tmdb_movies:
            try:
                # Extract genres
                genres = []
                if 'genres' in movie and isinstance(movie['genres'], list):
                    genres = [g.get('name', '') for g in movie['genres']]
                genres_str = '|'.join(genres) if genres else ''
                
                # Extract directors
                directors = []
                cast_members = []
                
                if 'credits' in movie:
                    # Extract directors
                    if 'crew' in movie['credits']:
                        for crew in movie['credits']['crew']:
                            if crew.get('job') == 'Director':
                                directors.append(crew.get('name', ''))
                    
                    # Extract cast
                    if 'cast' in movie['credits']:
                        cast_members = [c.get('name', '') for c in movie['credits']['cast'][:5]]  # Top 5 cast
                
                # Extract language
                language_code = movie.get('original_language', 'en')
                language_name = LANGUAGE_PREFERENCES.get(language_code, 'Unknown')
                region = LANGUAGE_TO_REGION.get(language_code, 'International')
                
                # Create movie entry
                movie_id = str(movie.get('id', ''))
                tmdb_data.append({
                    'item_id': movie_id,  # Add item_id field to match database expectations
                    'title': movie.get('title', ''),
                    'genres': genres_str,
                    'directors': '|'.join(directors),
                    'cast': '|'.join(cast_members),
                    'vote_average': movie.get('vote_average', 0.0),
                    'vote_count': movie.get('vote_count', 0),
                    'popularity': movie.get('popularity', 0.0),
                    'is_trending': 1 if movie.get('popularity', 0) > 30 else 0,  # Mark popular movies as trending
                    'overview': movie.get('overview', ''),
                    'language': language_name,
                    'imdb_id': movie.get('imdb_id', ''),
                    'tmdb_id': movie_id,
                    'movielens_id': '',  # We're not using MovieLens
                    'language_code': language_code,
                    'region': region,
                    'release_date': movie.get('release_date', '')
                })
            except Exception as e:
                logger.error(f"Error processing movie {movie.get('id', 'unknown')}: {e}")
        
        # Create DataFrame
        items_df = pd.DataFrame(tmdb_data)
        
        # Extract year from release_date if available
        items_df['year'] = items_df['release_date'].str[:4]
        
        # Save to CSV
        items_df.to_csv(PROCESSED_DIR / 'movies.csv', index=False)
        
        logger.info(f"Processed {len(items_df)} TMDB movies")
        
        return items_df, None
    
    except Exception as e:
        logger.error(f"Error processing TMDB dataset: {e}")
        return None, None

def create_users_df(n_users=500):
    """
    Create a DataFrame of users with demographic information.
    
    Args:
        n_users: Number of users to create
        
    Returns:
        DataFrame: Users with demographic information
    """
    logger.info("Creating users dataframe with demographics...")
    
    # Create user IDs
    users = pd.DataFrame({
        'user_id': range(1, n_users + 1)
    })
    
    # Add demographic information
    users['age'] = np.random.normal(35, 12, size=len(users)).astype(int)
    users['age'] = users['age'].clip(18, 80)  # Clip ages to a reasonable range
    
    # Add gender (binary for simplicity)
    users['gender'] = np.random.choice(['M', 'F'], size=len(users))
    
    # Add occupation (using simple categories)
    occupations = ['Student', 'Professional', 'Manager', 'Engineer', 'Artist', 'Healthcare', 'Service', 'Retired', 'Other']
    users['occupation'] = np.random.choice(occupations, size=len(users))
    
    # Add location to help with local language recommendations
    # Focus on Indian locations to prioritize Indian language movies
    indian_locations = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Kolkata', 'Pune', 'Ahmedabad', 
                      'Jaipur', 'Lucknow', 'Chandigarh', 'Kochi', 'Bhopal', 'Indore', 'Surat']
    international_locations = ['New York', 'London', 'Tokyo', 'Paris', 'Berlin', 'Madrid', 'Seoul', 'Beijing']
    
    # Create location distribution biased toward Indian locations (70% Indian, 30% international)
    locations = []
    for _ in range(len(users)):
        if np.random.random() < 0.7:
            locations.append(np.random.choice(indian_locations))
        else:
            locations.append(np.random.choice(international_locations))
    
    users['location'] = locations
    
    # Assign language preferences based on location
    # Map locations to likely language preferences
    location_to_language = {
        'Mumbai': ['hi', 'mr'],
        'Delhi': ['hi'],
        'Bangalore': ['kn', 'hi', 'en'],
        'Chennai': ['ta'],
        'Hyderabad': ['te', 'hi'],
        'Kolkata': ['bn'],
        'Pune': ['mr', 'hi'],
        'Ahmedabad': ['gu', 'hi'],
        'Jaipur': ['hi'],
        'Lucknow': ['hi'],
        'Chandigarh': ['hi', 'pa'],
        'Kochi': ['ml'],
        'Bhopal': ['hi'],
        'Indore': ['hi'],
        'Surat': ['gu', 'hi'],
        'New York': ['en'],
        'London': ['en'],
        'Tokyo': ['ja', 'en'],
        'Paris': ['fr', 'en'],
        'Berlin': ['de', 'en'],
        'Madrid': ['es', 'en'],
        'Seoul': ['ko', 'en'],
        'Beijing': ['zh', 'en']
    }
    
    # Function to assign language preferences based on location
    def get_language_prefs(location):
        primary_languages = location_to_language.get(location, ['en'])
        primary = np.random.choice(primary_languages)
        secondary = 'en' if primary != 'en' else np.random.choice(['hi', 'es', 'fr'])
        return primary, secondary
    
    # Assign language preferences
    languages = [get_language_prefs(loc) for loc in users['location']]
    users['language_preference'] = [lang[0] for lang in languages]
    users['secondary_language'] = [lang[1] for lang in languages]
    
    # Add language preference as text
    users['language_preference_name'] = users['language_preference'].map(LANGUAGE_PREFERENCES)
    users['secondary_language_name'] = users['secondary_language'].map(LANGUAGE_PREFERENCES)
    
    # Save to CSV
    users.to_csv(PROCESSED_DIR / 'users.csv', index=False)
    
    logger.info(f"Created {len(users)} users")
    
    return users

def create_interactions(items_df, users_df, n_interactions_per_user=10, rating_bias=0.5):
    """
    Create simulated user-movie interactions.
    
    Args:
        items_df: DataFrame of movies
        users_df: DataFrame of users
        n_interactions_per_user: Average number of interactions per user
        rating_bias: Positive bias in ratings (higher values = more positive ratings)
        
    Returns:
        DataFrame: User-movie interactions
    """
    logger.info("Creating simulated interactions...")
    
    if items_df is None or users_df is None:
        logger.error("Cannot create interactions: items_df or users_df is None")
        return None
    
    interactions = []
    
    for _, user in users_df.iterrows():
        user_id = user['user_id']
        n_interactions = max(1, int(np.random.normal(n_interactions_per_user, n_interactions_per_user / 2)))
        
        # Find movies in user's preferred language if possible
        preferred_language = user['language_preference']
        secondary_language = user['secondary_language']
        
        # Filter movies by language preference
        preferred_movies = items_df[items_df['language_code'] == preferred_language]
        secondary_movies = items_df[items_df['language_code'] == secondary_language]
        
        # If not enough movies in preferred language, include some in secondary language
        # If still not enough, use any language
        if len(preferred_movies) < n_interactions * 0.7:
            combined_movies = pd.concat([preferred_movies, secondary_movies])
            if len(combined_movies) < n_interactions * 0.7:
                movie_pool = items_df
            else:
                movie_pool = combined_movies
        else:
            movie_pool = preferred_movies
        
        # Sample movies for this user
        if len(movie_pool) > 0:
            # Sample with replacement if necessary
            if len(movie_pool) < n_interactions:
                sampled_movies = movie_pool.sample(n_interactions, replace=True)
            else:
                sampled_movies = movie_pool.sample(n_interactions)
            
            # Generate interactions
            for _, movie in sampled_movies.iterrows():
                # Generate a rating biased toward positive (most people watch movies they think they'll like)
                # Adjust based on whether the movie is in their preferred language
                lang_match = movie['language_code'] == preferred_language
                lang_bonus = 0.5 if lang_match else 0.0
                
                rating = min(5, max(0.5, np.random.normal(3.5 + rating_bias + lang_bonus, 0.8)))
                rating = round(rating * 2) / 2  # Round to nearest 0.5
                
                # Generate contextual data
                moods = ['happy', 'sad', 'neutral', 'excited', 'relaxed']
                times_of_day = ['morning', 'afternoon', 'evening', 'night']
                days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weather_conditions = ['sunny', 'cloudy', 'rainy', 'snowy', 'clear']
                
                interaction = {
                    'userId': user_id,
                    'movieId': int(movie['tmdb_id']) if movie['tmdb_id'].isdigit() else 0,  # Use TMDB ID as movie ID
                    'rating': rating,
                    'timestamp': int(np.random.randint(1577836800, 1672531200)),  # Random timestamp between 2020-01-01 and 2023-01-01
                    'mood': np.random.choice(moods),
                    'time_of_day': np.random.choice(times_of_day),
                    'day_of_week': np.random.choice(days_of_week),
                    'weather': np.random.choice(weather_conditions),
                    'event_type': 'watch'
                }
                interactions.append(interaction)
    
    # Convert to DataFrame
    interactions_df = pd.DataFrame(interactions)
    
    # Rename columns to match what database.py expects
    interactions_df = interactions_df.rename(columns={
        'userId': 'user_id',
        'movieId': 'item_id',
        'rating': 'sentiment_score'
    })
    
    # Save to CSV
    interactions_df.to_csv(PROCESSED_DIR / 'interactions.csv', index=False)
    
    logger.info(f"Created {len(interactions_df)} interactions")
    
    return interactions_df

def preprocess_data(downloaded_data):
    """
    Main preprocessing function.
    
    Args:
        downloaded_data: Dictionary containing paths to downloaded data
        
    Returns:
        dict: Dictionary containing processed DataFrames
    """
    logger.info("Starting data preprocessing...")
    
    # Create directories
    create_directories()
    
    # Get sample size if provided
    sample_size = downloaded_data.get('sample_size')
    if sample_size:
        logger.info(f"Using sample size of {sample_size}")
    
    # Process TMDB dataset
    tmdb_dir = downloaded_data.get('tmdb_dir', RAW_DIR)
    items_df, _ = process_tmdb_dataset(tmdb_dir)
    
    # Create users
    users_df = create_users_df(n_users=sample_size if sample_size else 500)
    
    # Create interactions
    interactions_df = create_interactions(items_df, users_df)
    
    return {
        'items_df': items_df,
        'users_df': users_df,
        'interactions_df': interactions_df
    }

if __name__ == "__main__":
    # For testing
    from download import download_all_datasets
    downloaded_data = download_all_datasets()
    preprocess_data(downloaded_data) 