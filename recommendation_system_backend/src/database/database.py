import sqlite3
import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/database.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path('data/processed/recommendation.db')

def get_db_connection():
    """Create a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the required tables."""
    logger.info("Initializing database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
    
    # Create Interactions table
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
        event_type TEXT,
        FOREIGN KEY (user_id) REFERENCES UserProfiles (user_id),
        FOREIGN KEY (item_id) REFERENCES Items (item_id)
    )
    ''')
    
    # Create indices for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON Interactions (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_item_id ON Interactions (item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON Interactions (timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_genres ON Items (genres)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_release_year ON Items (release_year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_popularity ON Items (popularity)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_language ON Items (language)')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def add_user(user_id, age=None, age_group=None, location=None, language_preference=None, preferred_genres=None):
    """Add a new user to the UserProfiles table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert list of genres to pipe-separated string if needed
    if preferred_genres and isinstance(preferred_genres, list):
        preferred_genres = '|'.join(preferred_genres)
    
    cursor.execute('''
    INSERT OR REPLACE INTO UserProfiles (user_id, age, age_group, location, language_preference, preferred_genres)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, age, age_group, location, language_preference, preferred_genres))
    
    conn.commit()
    conn.close()
    logger.info(f"Added user: {user_id}")

def add_item(item_id, title, title_type=None, genres=None, release_year=None, 
             runtime_minutes=None, vote_average=None, vote_count=None, 
             popularity=None, is_trending=0, overview=None, language=None,
             imdb_id=None, tmdb_id=None, movielens_id=None):
    """Add a new item to the Items table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO Items (
        item_id, title, title_type, genres, release_year, runtime_minutes,
        vote_average, vote_count, popularity, is_trending, overview,
        language, imdb_id, tmdb_id, movielens_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        item_id, title, title_type, genres, release_year, runtime_minutes,
        vote_average, vote_count, popularity, is_trending, overview,
        language, imdb_id, tmdb_id, movielens_id
    ))
    
    conn.commit()
    conn.close()
    logger.info(f"Added item: {item_id} - {title}")

def add_interaction(user_id, item_id, sentiment_score=None, mood=None, 
                   age=None, time_of_day=None, day_of_week=None, 
                   weather=None, location=None, event_type="watch"):
    """Add a new interaction to the Interactions table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO Interactions (
        user_id, item_id, sentiment_score, mood, age,
        time_of_day, day_of_week, weather, location, event_type
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, item_id, sentiment_score, mood, age,
        time_of_day, day_of_week, weather, location, event_type
    ))
    
    conn.commit()
    conn.close()
    logger.info(f"Added interaction: {user_id} - {item_id}")

def get_user_interactions(user_id, limit=100):
    """Get interactions for a specific user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT i.*, it.title, it.genres
    FROM Interactions i
    JOIN Items it ON i.item_id = it.item_id
    WHERE i.user_id = ?
    ORDER BY i.timestamp DESC
    LIMIT ?
    ''', (user_id, limit))
    
    interactions = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in interactions]

def get_item_details(item_id):
    """Get details for a specific item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM Items WHERE item_id = ?', (item_id,))
    item = cursor.fetchone()
    
    conn.close()
    
    return dict(item) if item else None

def get_similar_items_by_genre(genres, limit=20, exclude_item_id=None):
    """Get items with similar genres."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    genre_pattern = '%' + genres + '%'
    
    query = '''
    SELECT * FROM Items 
    WHERE genres LIKE ? 
    '''
    
    params = [genre_pattern]
    
    if exclude_item_id:
        query += 'AND item_id != ? '
        params.append(exclude_item_id)
    
    query += '''
    ORDER BY popularity DESC, vote_average DESC
    LIMIT ?
    '''
    params.append(limit)
    
    cursor.execute(query, params)
    items = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in items]

def get_trending_items(limit=20):
    """Get trending items."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM Items
    WHERE is_trending = 1
    ORDER BY popularity DESC
    LIMIT ?
    ''', (limit,))
    
    items = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in items]

def get_all_users():
    """Get all users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM UserProfiles')
    users = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in users]

def get_all_items(limit=None):
    """Get all items with optional limit."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('SELECT * FROM Items LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT * FROM Items')
    
    items = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in items]

def get_all_interactions(limit=None):
    """Get all interactions with optional limit."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('SELECT * FROM Interactions LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT * FROM Interactions')
    
    interactions = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in interactions]

def execute_query(query, params=()):
    """Execute a custom query."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(query, params)
    
    if query.strip().upper().startswith('SELECT'):
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    else:
        conn.commit()
        conn.close()
        return True

def load_data_from_csv():
    """Load data from CSV files into the database."""
    logger.info("Loading data from CSV files into the database...")
    
    try:
        # Create a single connection for the entire process
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Load movies data
        movies_path = Path('data/processed/movies.csv')
        if os.path.exists(movies_path):
            movies_df = pd.read_csv(movies_path)
            logger.info(f"Loaded {len(movies_df)} movies from CSV")
            
            # Add each movie to the database
            for _, row in movies_df.iterrows():
                try:
                    cursor.execute('''
                    INSERT OR IGNORE INTO Items (
                        item_id, title, genres, release_year, popularity
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row['item_id'], 
                        row['title'],
                        row.get('genres', ''),
                        row.get('release_year', None),
                        row.get('popularity', 0.0)
                    ))
                except Exception as e:
                    logger.error(f"Error adding movie {row['item_id']}: {e}")
            
            conn.commit()
            logger.info("Movies data loaded into database")
        else:
            logger.warning(f"Movies CSV file not found at {movies_path}")
        
        # Load interactions data
        interactions_path = Path('data/processed/interactions.csv')
        if os.path.exists(interactions_path):
            interactions_df = pd.read_csv(interactions_path)
            logger.info(f"Loaded {len(interactions_df)} interactions from CSV")
            
            # Process interactions in batches to avoid locking
            batch_size = 1000
            total_interactions = len(interactions_df)
            
            for i in range(0, total_interactions, batch_size):
                end_idx = min(i + batch_size, total_interactions)
                batch = interactions_df.iloc[i:end_idx]
                
                logger.info(f"Processing interactions batch {i+1} to {end_idx} of {total_interactions}")
                
                for _, row in batch.iterrows():
                    try:
                        cursor.execute('''
                        INSERT OR IGNORE INTO Interactions (
                            user_id, item_id, timestamp, sentiment_score, 
                            mood, time_of_day, day_of_week, weather, event_type
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row['user_id'],
                            row['item_id'],
                            row.get('timestamp', None),
                            row.get('sentiment_score', 0.5),
                            row.get('mood', None),
                            row.get('time_of_day', None),
                            row.get('day_of_week', None),
                            row.get('weather', None),
                            row.get('event_type', 'watch')
                        ))
                    except Exception as e:
                        logger.error(f"Error adding interaction for user {row['user_id']} and item {row['item_id']}: {e}")
                
                # Commit after each batch
                conn.commit()
            
            logger.info("Interactions data loaded into database")
        else:
            logger.warning(f"Interactions CSV file not found at {interactions_path}")
        
        # Close the connection at the end
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error loading data from CSV: {e}")
        return False

def setup_database():
    """Initialize the database and load data from CSV files."""
    # Initialize the database structure
    init_db()
    
    # Load data from CSV files
    load_data_from_csv()
    
    logger.info("Database setup completed successfully.")

if __name__ == "__main__":
    # Initialize the database
    setup_database() 