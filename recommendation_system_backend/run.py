#!/usr/bin/env python3
"""
Main runner script for the local recommendation system.
"""

import os
import sys
import argparse
import logging
import sqlite3
import time
import datetime
from pathlib import Path

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(script_dir, "logs/runner.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Create necessary directories if they don't exist."""
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    logger.info("Environment setup complete")

def run_preprocess(sample_size=None):
    """
    Run data preprocessing.
    
    Args:
        sample_size (int, optional): Number of rows to process
    """
    logger.info("Running data preprocessing...")
    
    from src.database.preprocess import preprocess_data
    
    # Import the download function to get the data paths
    from src.database.download import download_all_datasets
    
    # Download datasets if needed and get their paths
    downloaded_data = download_all_datasets()
    
    # Store sample_size in downloaded_data dict if provided
    if sample_size is not None:
        downloaded_data['sample_size'] = sample_size
    
    # Run preprocessing
    preprocess_data(downloaded_data)
    
    logger.info("Data preprocessing complete")

def train_models():
    """Train recommendation models."""
    logger.info("Training recommendation models...")
    
    from src.models.train_models import main as train_models_main
    
    train_models_main()
    
    logger.info("Model training complete")

def setup_database():
    """Set up the SQLite database schema."""
    try:
        db_path = os.path.join(script_dir, "data/processed/recommendation.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create recommendation cache table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendation_cache (
            cache_key TEXT PRIMARY KEY,
            recommendations TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database schema setup complete")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")

def clean_recommendation_cache():
    """Clean old entries from recommendation cache."""
    try:
        db_path = os.path.join(script_dir, "data/processed/recommendation.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete cache entries older than 24 hours
        current_time = datetime.datetime.now().isoformat()
        cursor.execute(
            "DELETE FROM recommendation_cache WHERE datetime(created_at) < datetime('now', '-1 day')"
        )
        
        conn.commit()
        conn.close()
        logger.info("Cleaned recommendation cache")
    except Exception as e:
        logger.error(f"Error cleaning recommendation cache: {e}")

def run_api():
    """Run the API server."""
    try:
        # Set up database if needed
        setup_database()
        
        # Clean recommendation cache
        clean_recommendation_cache()
        
        # Import and start the API
        from src.api.main import start
        logger.info("Starting API server...")
        start()
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        sys.exit(1)

def main():
    """Main function to run the recommendation system."""
    parser = argparse.ArgumentParser(description='Run the local recommendation system')
    
    parser.add_argument('--step', choices=['all', 'preprocess', 'train', 'api'], default='all',
                      help='Which step to run (default: all)')
    
    parser.add_argument('--sample', type=int,
                      help='Number of rows to process for each dataset')
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    if args.step in ['all', 'preprocess']:
        run_preprocess(sample_size=args.sample)
    
    if args.step in ['all', 'train']:
        train_models()
    
    if args.step in ['all', 'api']:
        run_api()

if __name__ == "__main__":
    main() 
