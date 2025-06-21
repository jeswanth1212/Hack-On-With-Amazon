#!/usr/bin/env python3

import os
import sys
import logging
import importlib
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("__main__")

def setup_environment():
    """Set up the environment."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create data directories if they don't exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/processed/models", exist_ok=True)
    
    # Add the project directory to the path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    logger.info("Environment setup complete")
    
    return True

def reset_database():
    """Reset the database by deleting it."""
    db_path = "data/processed/recommendation.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Deleted existing database at {db_path}")
    
    # Delete any other database files
    for filename in os.listdir("data/processed"):
        if filename.endswith(".db") or filename.endswith(".sqlite"):
            file_path = os.path.join("data/processed", filename)
            os.remove(file_path)
            logger.info(f"Deleted {file_path}")
    
    # Reset model files
    model_dir = "data/processed/models"
    if os.path.exists(model_dir):
        shutil.rmtree(model_dir)
        os.makedirs(model_dir, exist_ok=True)
        logger.info("Reset model directory")
    
    return True

def process_data():
    """Run data processing."""
    logger.info("Running data preprocessing...")
    
    try:
        # Import the modules
        from src.database import download, preprocess
        
        # Download datasets
        downloaded_data = download.download_all_datasets()
        
        # Process datasets
        processed_data = preprocess.preprocess_data(downloaded_data)
        
        # Initialize the database with processed data
        from src.database.database import initialize_database, load_data_to_db
        
        # Initialize the database
        db_initialized = initialize_database()
        
        if db_initialized:
            # Load data into the database
            load_data_to_db()
            logger.info("Database setup completed successfully")
            return True
        else:
            logger.error("Database initialization failed")
            return False
        
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return False

def main():
    """Main function."""
    try:
        # Set up environment
        if not setup_environment():
            return False
        
        # Reset database
        if not reset_database():
            return False
        
        # Process data
        if not process_data():
            return False
        
        logger.info("Reset and setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in reset_and_setup: {e}")
        return False

if __name__ == "__main__":
    main() 