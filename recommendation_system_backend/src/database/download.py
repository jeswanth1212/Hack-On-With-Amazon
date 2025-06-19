import os
import logging
import requests
import zipfile
import pandas as pd
from pathlib import Path
from tqdm import tqdm

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

# URLs for datasets
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
TMDB_MOVIES_URL = "https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata/download"  # Note: Requires Kaggle authentication

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
    """Download and extract the MovieLens dataset."""
    ensure_data_dirs()
    
    # Define paths
    zip_path = RAW_DATA_DIR / "ml-latest-small.zip"
    
    # Download the dataset
    download_file(MOVIELENS_URL, zip_path)
    
    # Extract the dataset
    extract_zip(zip_path, RAW_DATA_DIR)
    
    # Check if the extraction created the expected directory
    ml_dir = RAW_DATA_DIR / "ml-latest-small"
    if ml_dir.exists():
        logger.info(f"MovieLens dataset extracted to {ml_dir}")
        return ml_dir
    else:
        logger.error("MovieLens dataset extraction failed")
        return None

def download_tmdb(api_key=None):
    """
    Download TMDB dataset using Kaggle API.
    
    Args:
        api_key (str, optional): Kaggle API key
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        
        # Check if Kaggle API is configured
        api = KaggleApi()
        api.authenticate()
        
        # Download the dataset
        logger.info("Downloading TMDB dataset from Kaggle")
        api.dataset_download_files('tmdb/tmdb-movie-metadata', path=RAW_DATA_DIR, unzip=True)
        
        tmdb_dir = RAW_DATA_DIR
        logger.info(f"TMDB dataset downloaded to {tmdb_dir}")
        return tmdb_dir
        
    except Exception as e:
        logger.error(f"Failed to download TMDB dataset: {e}")
        logger.info("Skipping TMDB dataset. Using MovieLens only.")
        return None

def download_all_datasets():
    """Download all required datasets."""
    logger.info("Starting dataset downloads")
    
    # Create data directories if they don't exist
    ensure_data_dirs()
    
    # Download MovieLens dataset
    movielens_dir = download_movielens()
    
    # Try to download TMDB dataset
    tmdb_dir = None
    try:
        tmdb_dir = download_tmdb()
    except Exception as e:
        logger.warning(f"TMDB download failed, continuing with MovieLens only: {e}")
    
    return {
        "movielens_dir": movielens_dir,
        "tmdb_dir": tmdb_dir
    }

if __name__ == "__main__":
    download_all_datasets() 