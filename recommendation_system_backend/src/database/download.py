import os
import logging
import requests
import zipfile
import pandas as pd
import json
import time
import random
from pathlib import Path
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/download.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define data directories
RAW_DATA_DIR = Path('data/raw')
PROCESSED_DATA_DIR = Path('data/processed')
TMDB_API_KEY = "ee41666274420bb7514d6f2f779b5fd9"  # Using the same API key as frontend

# Languages to include - focusing on Indian languages
INDIAN_LANGUAGES = [
    "hi",    # Hindi
    "ta",    # Tamil
    "te",    # Telugu
    "ml",    # Malayalam
    "kn",    # Kannada
    "bn",    # Bengali
    "mr",    # Marathi
    "pa",    # Punjabi
    "gu",    # Gujarati
    "or",    # Odia
    "as"     # Assamese
]

# Include English and some other popular languages
OTHER_LANGUAGES = [
    "en",    # English
    "ja",    # Japanese
    "ko",    # Korean
    "zh",    # Chinese
    "fr",    # French
    "es",    # Spanish
    "de",    # German
]

ALL_LANGUAGES = INDIAN_LANGUAGES + OTHER_LANGUAGES

def ensure_data_dirs():
    """Ensure data directories exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories created.")

def download_file(url, destination):
    """
    Download a file with progress tracking.
    
    Args:
        url (str): URL to download
        destination (Path): Destination file path
    """
    logger.info(f"Downloading {url} to {destination}")
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    
    with open(destination, 'wb') as file, tqdm(
            desc=os.path.basename(destination),
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
        for data in response.iter_content(block_size):
            size = file.write(data)
            bar.update(size)
    
    logger.info(f"Download complete: {destination}")

def extract_zip(zip_path, extract_to):
    """
    Extract a zip file.
    
    Args:
        zip_path (Path): Path to zip file
        extract_to (Path): Directory to extract to
    """
    logger.info(f"Extracting {zip_path} to {extract_to}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    logger.info(f"Extraction complete: {zip_path}")

def download_movielens():
    """
    Download MovieLens dataset.
    Note: This is kept for backward compatibility but won't be used in the final system.
    """
    logger.info("MovieLens dataset will not be used in the new system.")
    return None

def create_session_with_retries():
    """
    Create a requests session with retry capabilities.
    """
    session = requests.Session()
    # Configure retries: retry on connection errors, status codes 429 (too many requests) and 500s
    retries = Retry(
        total=5,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def fetch_tmdb_movies_by_language_page(session, language_code, page=1, max_retries=3, delay=1.0):
    """
    Fetch a single page of movies from TMDB API for a specific language.
    
    Args:
        session: Requests session with retries
        language_code (str): Language code (e.g., 'hi' for Hindi)
        page (int): Page number
        max_retries (int): Maximum number of retries
        delay (float): Base delay between retries in seconds
        
    Returns:
        list: List of movie IDs
    """
    base_url = "https://api.themoviedb.org/3"
    discover_url = f"{base_url}/discover/movie?api_key={TMDB_API_KEY}&with_original_language={language_code}&page={page}&sort_by=popularity.desc"
    
    for retry in range(max_retries):
        try:
            # Add a small random delay to avoid hitting rate limits
            time.sleep(delay + random.random())
            
            response = session.get(discover_url, timeout=10)
            response.raise_for_status()
            
            results = response.json().get('results', [])
            logger.info(f"Fetched {len(results)} movies for language {language_code} (page {page})")
            
            movie_ids = [movie.get('id') for movie in results if movie.get('id')]
            return movie_ids
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching page {page} for language {language_code} (attempt {retry+1}/{max_retries}): {e}")
            # Exponential backoff with jitter
            time.sleep(delay * (2 ** retry) + random.random())
    
    logger.error(f"Failed to fetch page {page} for language {language_code} after {max_retries} attempts")
    return []

def fetch_movie_details(session, movie_id, max_retries=3, delay=1.0):
    """
    Fetch detailed information for a single movie.
    
    Args:
        session: Requests session with retries
        movie_id (int): TMDB movie ID
        max_retries (int): Maximum number of retries
        delay (float): Base delay between retries in seconds
        
    Returns:
        dict: Movie details or None if failed
    """
    base_url = "https://api.themoviedb.org/3"
    details_url = f"{base_url}/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
    
    for retry in range(max_retries):
        try:
            # Add a small random delay to avoid hitting rate limits
            time.sleep(delay + random.random())
            
            response = session.get(details_url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching details for movie ID {movie_id} (attempt {retry+1}/{max_retries}): {e}")
            # Exponential backoff with jitter
            time.sleep(delay * (2 ** retry) + random.random())
    
    logger.error(f"Failed to fetch details for movie ID {movie_id} after {max_retries} attempts")
    return None

def fetch_tmdb_movies_by_language(language_code, pages=5, movies_per_language=50):
    """
    Fetch movies from TMDB API for a specific language.
    
    Args:
        language_code (str): Language code (e.g., 'hi' for Hindi)
        pages (int): Maximum number of pages to fetch
        movies_per_language (int): Maximum number of movies to fetch per language
        
    Returns:
        list: List of movie data
    """
    movies = []
    movie_ids = []
    session = create_session_with_retries()
    
    try:
        # Phase 1: Collect movie IDs from discovery API
        for page in range(1, pages + 1):
            if len(movie_ids) >= movies_per_language:
                break
                
            page_movie_ids = fetch_tmdb_movies_by_language_page(session, language_code, page)
            if not page_movie_ids:
                break
                
            movie_ids.extend(page_movie_ids)
            logger.info(f"Collected {len(movie_ids)} total movie IDs for language {language_code}")
            
            # Stop if we've hit our target number of movies
            if len(movie_ids) >= movies_per_language:
                movie_ids = movie_ids[:movies_per_language]
                break
        
        # Phase 2: Fetch detailed information for each movie
        for movie_id in movie_ids:
            movie_details = fetch_movie_details(session, movie_id)
            if movie_details:
                movies.append(movie_details)
                
        logger.info(f"Fetched {len(movies)} detailed movie entries for language {language_code}")
        
    except Exception as e:
        logger.error(f"Error fetching TMDB movies for language {language_code}: {e}")
    
    return movies

def download_tmdb_direct():
    """
    Download movies from TMDB API directly, focusing on Indian languages.
    
    Returns:
        Path: Path to saved TMDB data
    """
    try:
        tmdb_file = RAW_DATA_DIR / 'tmdb_movies.json'
        if tmdb_file.exists():
            logger.info("TMDB data already exists, skipping download")
            return Path(RAW_DATA_DIR)
    
        logger.info("Starting direct TMDB API download")
        
        all_movies = []
        
        # Define how many movies to fetch per language
        indian_movies_per_language = 50   # More Indian movies
        other_movies_per_language = 25    # Fewer non-Indian movies
        
        # First fetch Indian language movies (with more pages)
        for language in INDIAN_LANGUAGES:
            logger.info(f"Fetching movies for Indian language: {language}")
            language_movies = fetch_tmdb_movies_by_language(language, pages=10, movies_per_language=indian_movies_per_language)
            all_movies.extend(language_movies)
            logger.info(f"Fetched {len(language_movies)} movies for language {language}")
        
        # Then fetch other language movies
        for language in OTHER_LANGUAGES:
            logger.info(f"Fetching movies for language: {language}")
            language_movies = fetch_tmdb_movies_by_language(language, pages=5, movies_per_language=other_movies_per_language)
            all_movies.extend(language_movies)
            logger.info(f"Fetched {len(language_movies)} movies for language {language}")
        
        # Save the data
        output_file = RAW_DATA_DIR / 'tmdb_movies.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(all_movies)} TMDB movies to {output_file}")
        return RAW_DATA_DIR
    
    except Exception as e:
        logger.error(f"Error in direct TMDB download: {e}")
        return None

def process_existing_tmdb_files():
    """
    Process existing TMDB CSV files as a fallback when direct API download fails.
    
    Returns:
        list: List of processed movie data
    """
    try:
        logger.info("Processing existing TMDB CSV files as fallback")
        
        movies_file = RAW_DATA_DIR / "tmdb_5000_movies.csv"
        credits_file = RAW_DATA_DIR / "tmdb_5000_credits.csv"
        
        if not (movies_file.exists() and credits_file.exists()):
            logger.error("Required TMDB CSV files not found")
            return None
        
        # Load and process the movies data
        movies_df = pd.read_csv(movies_file)
        credits_df = pd.read_csv(credits_file)
        
        # Rename id column in credits to movie_id for merging
        if 'movie_id' not in credits_df.columns and 'id' in credits_df.columns:
            credits_df = credits_df.rename(columns={'id': 'movie_id'})
        
        # Merge dataframes
        merged_df = movies_df.merge(credits_df, on='id', how='left')
        
        # Convert DataFrame to list of dictionaries (similar to TMDB API response)
        all_movies = []
        
        # Process each movie
        for _, row in merged_df.iterrows():
            try:
                # Parse JSON strings
                cast = json.loads(row.get('cast', '[]')) if isinstance(row.get('cast'), str) else []
                crew = json.loads(row.get('crew', '[]')) if isinstance(row.get('crew'), str) else []
                genres = json.loads(row.get('genres', '[]')) if isinstance(row.get('genres'), str) else []
                
                # Extract original language
                original_language = row.get('original_language', 'en')
                
                # Create movie entry
                movie = {
                    'id': row.get('id', 0),
                    'title': row.get('title', ''),
                    'original_title': row.get('original_title', ''),
                    'overview': row.get('overview', ''),
                    'release_date': row.get('release_date', ''),
                    'original_language': original_language,
                    'popularity': row.get('popularity', 0),
                    'vote_average': row.get('vote_average', 0),
                    'vote_count': row.get('vote_count', 0),
                    'genres': genres,
                    'credits': {
                        'cast': cast,
                        'crew': crew
                    }
                }
                
                all_movies.append(movie)
                
            except Exception as e:
                logger.error(f"Error processing movie {row.get('id', 'unknown')}: {e}")
        
        # Save the processed data
        output_file = RAW_DATA_DIR / 'tmdb_movies.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Processed {len(all_movies)} movies from existing TMDB CSV files")
        return all_movies
        
    except Exception as e:
        logger.error(f"Error processing existing TMDB files: {e}")
        return None

def download_all_datasets():
    """Download all required datasets."""
    logger.info("Starting dataset downloads")
    
    # Create data directories if they don't exist
    ensure_data_dirs()
    
    # Skip MovieLens download as per requirements
    movielens_dir = None
    
    # Try direct API download first
    tmdb_dir = download_tmdb_direct()
    
    # Check if we got enough movies from the direct download
    tmdb_json_file = RAW_DATA_DIR / 'tmdb_movies.json'
    if tmdb_json_file.exists():
        try:
            with open(tmdb_json_file, 'r', encoding='utf-8') as f:
                movies = json.load(f)
            
            # If we have less than 50 movies from direct API, use the CSV files instead
            if len(movies) < 50:
                logger.warning(f"Only found {len(movies)} movies from direct API. Using existing CSV files as fallback.")
                process_existing_tmdb_files()
        except Exception as e:
            logger.error(f"Error reading TMDB JSON file: {e}")
            process_existing_tmdb_files()
    else:
        logger.warning("No TMDB JSON file found from direct download. Using existing CSV files as fallback.")
        process_existing_tmdb_files()
    
    return {
        "movielens_dir": movielens_dir,
        "tmdb_dir": RAW_DATA_DIR
    }

if __name__ == "__main__":
    download_all_datasets() 