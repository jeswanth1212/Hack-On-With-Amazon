#!/usr/bin/env python3

import sqlite3
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_database")

# Database path
DB_PATH = Path('data/processed/recommendation.db')

def get_db_connection():
    """Create a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def fix_database():
    """Fix the database schema by ensuring all tables are properly created and referenced."""
    logger.info("Fixing database schema...")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file does not exist at {DB_PATH}")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, disable foreign keys to allow modifications
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    # Check if UserProfiles table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='UserProfiles';")
    if not cursor.fetchone():
        logger.info("UserProfiles table does not exist. Creating...")
        
        # Create UserProfiles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserProfiles (
            user_id TEXT PRIMARY KEY,
            age INTEGER,
            age_group TEXT,
            location TEXT,
            language_preference TEXT,
            preferred_genres TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    
    # Check if Items table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Items';")
    if not cursor.fetchone():
        logger.info("Items table does not exist. Creating...")
        
        # Create Items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Items (
            item_id TEXT PRIMARY KEY,
            title TEXT,
            title_type TEXT,
            genres TEXT,
            release_year INTEGER,
            runtime_minutes REAL,
            vote_average REAL,
            vote_count INTEGER,
            popularity REAL,
            is_trending INTEGER,
            overview TEXT,
            imdb_id TEXT,
            tmdb_id TEXT,
            movielens_id TEXT,
            language_code TEXT,
            language TEXT,
            region TEXT
        )
        ''')
    
    # Check if Interactions table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Interactions';")
    if cursor.fetchone():
        logger.info("Interactions table exists. Checking its structure...")
        # Drop and recreate Interactions table to fix foreign key issues
        cursor.execute("DROP TABLE Interactions;")
    
    # Create Interactions table with proper foreign keys
    logger.info("Creating Interactions table with proper foreign keys...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Interactions (
        interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        item_id TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sentiment_score REAL,
        mood TEXT,
        age INTEGER,
        time_of_day TEXT,
        day_of_week TEXT,
        weather TEXT,
        location TEXT,
        event_type TEXT
    )
    ''')
    
    # Check if recommendation_cache table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recommendation_cache';")
    if not cursor.fetchone():
        logger.info("recommendation_cache table does not exist. Creating...")
        
        # Create recommendation_cache table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendation_cache (
            cache_key TEXT PRIMARY KEY,
            recommendations TEXT,
            created_at TEXT
        )
        ''')
    
    # Create indices for faster queries
    logger.info("Creating indices...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON Interactions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_item_id ON Interactions (item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON Interactions (timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_genres ON Items (genres)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_release_year ON Items (release_year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_popularity ON Items (popularity)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_language ON Items (language)')
    
    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    conn.commit()
    conn.close()
    
    logger.info("Database schema fixed successfully.")
    return True

if __name__ == "__main__":
    fix_database() 