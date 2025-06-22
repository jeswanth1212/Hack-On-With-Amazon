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
        
        # Set up test watch party data for debugging
        test_watch_party_setup()
        
        # Check if port 8080 is in use and try to free it
        try:
            # Try to import and run the kill_port function
            from kill_port import kill_process_on_port
            kill_process_on_port(8080)
        except ImportError:
            logger.warning("kill_port.py not found. Cannot automatically free port 8080.")
            # Fallback to socket check
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8080))
            if result == 0:
                logger.warning("Port 8080 is already in use. Please stop any other services using this port.")
                logger.warning("Use 'netstat -ano | findstr :8080' to identify the process, then stop it.")
                # Continue anyway
            sock.close()
        
        # Start the API server with WebSocket support
        logger.info("Starting API server with WebSocket support...")
        logger.info("Server will be available at http://localhost:8080")
        logger.info("WebSocket will be available at ws://localhost:8080/socket.io/")
        
        import uvicorn
        
        # Configure and run uvicorn with explicit host and port
        uvicorn.run(
            "src.api.main:app", 
            host="0.0.0.0", 
            port=8080, 
            reload=False,  # Set to False to avoid conflicts with multiple processes
            ws_max_size=16777216,  # 16MB max WebSocket message size
            ws_ping_interval=20.0,  # Send pings to client every 20 seconds
            ws_ping_timeout=30.0,   # Wait up to 30 seconds for pings
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting API server: {e}")
        sys.exit(1)

def test_watch_party_setup():
    """Set up test watch party data for debugging."""
    logger.info("Setting up test watch party data...")
    
    try:
        from src.database.database import get_db_connection, create_watch_party, accept_watch_party
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if we already have watch parties
        cursor.execute("SELECT COUNT(*) FROM WatchParties")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create a test party with ID 1
            logger.info("Creating test watch party...")
            party_id = create_watch_party("user1", 299536, ["user2", "user3"])  # Avengers: Infinity War
            logger.info(f"Created test watch party with ID: {party_id}")
            
            # Accept invitations
            accept_watch_party(party_id, "user2")
            logger.info(f"User2 accepted invitation to party {party_id}")
            
            # Create another test party with ID 2
            party_id2 = create_watch_party("user2", 24428, ["user1", "user3"])  # The Avengers
            logger.info(f"Created test watch party with ID: {party_id2}")
            
            # Create a party with ID 3
            party_id3 = create_watch_party("user3", 299534, ["user1", "user2"])  # Avengers: Endgame
            logger.info(f"Created test watch party with ID: {party_id3}")
            
            logger.info("Test watch party data setup complete.")
        else:
            logger.info(f"Watch parties already exist in database ({count} parties).")
        
        conn.close()
    except Exception as e:
        logger.error(f"Error setting up test watch party data: {e}")

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
