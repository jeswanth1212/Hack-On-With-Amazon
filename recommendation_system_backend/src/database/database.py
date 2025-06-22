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
        event_type TEXT
    )
    ''')
    
    # Create recommendation_cache table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendation_cache (
        cache_key TEXT PRIMARY KEY,
        recommendations TEXT,
        created_at TEXT
    )
    ''')
    
    # Create Friendships table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Friendships (
        friendship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id_1 TEXT,
        user_id_2 TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id_1, user_id_2),
        FOREIGN KEY (user_id_1) REFERENCES UserProfiles (user_id),
        FOREIGN KEY (user_id_2) REFERENCES UserProfiles (user_id)
    )
    ''')
    
    # Create FriendRequests table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS FriendRequests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id TEXT,
        receiver_id TEXT,
        status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP,
        UNIQUE(sender_id, receiver_id),
        FOREIGN KEY (sender_id) REFERENCES UserProfiles (user_id),
        FOREIGN KEY (receiver_id) REFERENCES UserProfiles (user_id)
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
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friendships_user_id_1 ON Friendships (user_id_1)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friendships_user_id_2 ON Friendships (user_id_2)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friend_requests_sender ON FriendRequests (sender_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friend_requests_receiver ON FriendRequests (receiver_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_friend_requests_status ON FriendRequests (status)')
    
    # -----------------------------
    # Watch Party tables
    # -----------------------------
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS WatchParties (
        party_id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id TEXT,
        tmdb_id INTEGER,
        status TEXT CHECK(status IN ("pending", "active", "ended")) DEFAULT "pending",
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS WatchPartyParticipants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_id INTEGER,
        user_id TEXT,
        joined INTEGER DEFAULT 0,
        joined_at TIMESTAMP,
        FOREIGN KEY (party_id) REFERENCES WatchParties(party_id)
    )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchparty_participants_user ON WatchPartyParticipants(user_id)')
    
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

# Friend system functions
def search_users(query, current_user_id, limit=20):
    """
    Search for users by partial user_id match, excluding the current user.
    
    Args:
        query (str): The search query
        current_user_id (str): The current user's ID to exclude from results
        limit (int): Maximum number of results to return
        
    Returns:
        List of matching user profiles
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{query}%"
    
    cursor.execute('''
    SELECT * FROM UserProfiles 
    WHERE user_id LIKE ? AND user_id != ?
    LIMIT ?
    ''', (search_pattern, current_user_id, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

def send_friend_request(sender_id, receiver_id):
    """
    Send a friend request from sender to receiver.
    
    Args:
        sender_id (str): The ID of the user sending the request
        receiver_id (str): The ID of the user receiving the request
        
    Returns:
        bool: True if request was sent, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if there's an existing request in either direction
        cursor.execute('''
        SELECT * FROM FriendRequests 
        WHERE (sender_id = ? AND receiver_id = ?) 
        OR (sender_id = ? AND receiver_id = ?)
        ''', (sender_id, receiver_id, receiver_id, sender_id))
        
        existing_request = cursor.fetchone()
        if existing_request:
            logger.warning(f"Friend request already exists between {sender_id} and {receiver_id}")
            conn.close()
            return False
        
        # Check if they're already friends
        cursor.execute('''
        SELECT * FROM Friendships
        WHERE (user_id_1 = ? AND user_id_2 = ?) 
        OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (sender_id, receiver_id, receiver_id, sender_id))
        
        if cursor.fetchone():
            logger.warning(f"Users {sender_id} and {receiver_id} are already friends")
            conn.close()
            return False
            
        # Create the friend request
        cursor.execute('''
        INSERT INTO FriendRequests (sender_id, receiver_id, status)
        VALUES (?, ?, 'pending')
        ''', (sender_id, receiver_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Friend request sent from {sender_id} to {receiver_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending friend request: {e}")
        conn.close()
        return False

def respond_to_friend_request(request_id, status):
    """
    Respond to a friend request by updating its status.
    
    Args:
        request_id (int): The ID of the friend request
        status (str): The new status ('accepted' or 'rejected')
        
    Returns:
        bool: True if updated successfully, False otherwise
    """
    if status not in ['accepted', 'rejected']:
        logger.error(f"Invalid status: {status}")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update the request status
        cursor.execute('''
        UPDATE FriendRequests
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
        ''', (status, request_id))
        
        # If accepted, create friendship
        if status == 'accepted':
            # Get the request details
            cursor.execute('SELECT sender_id, receiver_id FROM FriendRequests WHERE request_id = ?', (request_id,))
            request = cursor.fetchone()
            
            if request:
                # Create two-way friendship
                cursor.execute('''
                INSERT INTO Friendships (user_id_1, user_id_2)
                VALUES (?, ?)
                ''', (request['sender_id'], request['receiver_id']))
                
                logger.info(f"Friendship created between {request['sender_id']} and {request['receiver_id']}")
        
        conn.commit()
        conn.close()
        logger.info(f"Friend request {request_id} {status}")
        return True
        
    except Exception as e:
        logger.error(f"Error responding to friend request: {e}")
        conn.close()
        return False

def get_pending_friend_requests(user_id):
    """
    Get all pending friend requests for a user.
    
    Args:
        user_id (str): The user's ID
        
    Returns:
        List of pending friend requests
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT fr.*, up.age, up.location, up.language_preference
    FROM FriendRequests fr
    JOIN UserProfiles up ON fr.sender_id = up.user_id
    WHERE fr.receiver_id = ? AND fr.status = 'pending'
    ''', (user_id,))
    
    requests = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in requests]

def get_friends(user_id):
    """
    Get all friends of a user.
    
    Args:
        user_id (str): The user's ID
        
    Returns:
        List of friend profiles
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT up.*, f.created_at as friendship_date
    FROM Friendships f
    JOIN UserProfiles up ON 
        CASE 
            WHEN f.user_id_1 = ? THEN up.user_id = f.user_id_2
            ELSE up.user_id = f.user_id_1
        END
    WHERE f.user_id_1 = ? OR f.user_id_2 = ?
    ''', (user_id, user_id, user_id))
    
    friends = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in friends]

def get_friend_activities(user_id, limit=50):
    """Get activities of a user's friends."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the user's friends
    cursor.execute('''
    SELECT user_id_2 as friend_id FROM Friendships WHERE user_id_1 = ?
    UNION
    SELECT user_id_1 as friend_id FROM Friendships WHERE user_id_2 = ?
    ''', (user_id, user_id))
    
    friends = [row['friend_id'] for row in cursor.fetchall()]
    
    if not friends:
        conn.close()
        return []
    
    # Get activities from friends
    placeholders = ','.join(['?'] * len(friends))
    query = f'''
    SELECT 
        i.user_id as friend_id,
        i.item_id,
        it.title,
        i.timestamp,
        it.genres,
        it.release_year,
        i.sentiment_score
    FROM Interactions i
    JOIN Items it ON i.item_id = it.item_id
    WHERE i.user_id IN ({placeholders})
    ORDER BY i.timestamp DESC
    LIMIT ?
    '''
    
    cursor.execute(query, friends + [limit])
    activities = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries and format timestamps
    result = []
    for row in activities:
        activity_dict = dict(row)
        # Convert timestamp to ISO format string if it's a number
        if isinstance(activity_dict['timestamp'], (int, float)):
            import datetime
            activity_dict['timestamp'] = datetime.datetime.fromtimestamp(
                activity_dict['timestamp']
            ).isoformat()
        result.append(activity_dict)
    
    return result

# ====================================================
# Watch Party helper functions
# ====================================================

def create_watch_party(host_id: str, tmdb_id: int, friend_ids: list[str]):
    """Create a new watch party and invitations."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('INSERT INTO WatchParties (host_id, tmdb_id) VALUES (?, ?)', (host_id, tmdb_id))
    party_id = cur.lastrowid

    # Add host as joined participant
    cur.execute('INSERT INTO WatchPartyParticipants (party_id, user_id, joined, joined_at) VALUES (?, ?, 1, CURRENT_TIMESTAMP)', (party_id, host_id))

    # Add friends as pending
    for fid in friend_ids:
        cur.execute('INSERT INTO WatchPartyParticipants (party_id, user_id, joined) VALUES (?, ?, 0)', (party_id, fid))

    conn.commit()
    conn.close()
    logger.info(f"Watch party {party_id} created by {host_id} for movie {tmdb_id}")
    return party_id


def get_watch_party_invites(user_id: str):
    """Return pending invites for user."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT wp.party_id, wp.host_id, wp.tmdb_id, wp.created_at
        FROM WatchPartyParticipants wpp
        JOIN WatchParties wp ON wp.party_id = wpp.party_id
        WHERE wpp.user_id = ? AND wpp.joined = 0 AND wp.status = "pending"
    ''', (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def accept_watch_party(party_id: int, user_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    # Update participant joined
    cur.execute('''
        UPDATE WatchPartyParticipants SET joined = 1, joined_at = CURRENT_TIMESTAMP
        WHERE party_id = ? AND user_id = ?
    ''', (party_id, user_id))

    # Check if all participants joined
    cur.execute('''
        SELECT COUNT(*) as total, SUM(joined) as joined_count FROM WatchPartyParticipants WHERE party_id = ?
    ''', (party_id,))
    res = cur.fetchone()
    if res and res['total'] == res['joined_count']:
        cur.execute('UPDATE WatchParties SET status = "active" WHERE party_id = ?', (party_id,))

    conn.commit()
    conn.close()
    logger.info(f"User {user_id} accepted party {party_id}")


def get_watch_party_details(party_id: int):
    """
    Get details of a watch party including participants.
    
    Args:
        party_id (int): ID of the watch party
        
    Returns:
        dict: Watch party details or None if not found
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Get watch party details
        cur.execute('SELECT * FROM WatchParties WHERE party_id = ?', (party_id,))
        party = cur.fetchone()
        if not party:
            return None
            
        # Convert to dictionary
        party_dict = dict(party)
        
        # Get participants
        cur.execute('SELECT user_id, joined, joined_at FROM WatchPartyParticipants WHERE party_id = ?', (party_id,))
        participants = [dict(r) for r in cur.fetchall()]
        party_dict['participants'] = participants
        
        return party_dict
    except Exception as e:
        print(f"Error getting watch party details: {e}")
        return None
    finally:
        conn.close()

def end_watch_party(party_id: int):
    """Mark a watch party as ended."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE WatchParties SET status = "ended" WHERE party_id = ?', (party_id,))
    conn.commit()
    conn.close()
    logger.info(f"Watch party {party_id} ended")

if __name__ == "__main__":
    # Initialize the database
    setup_database() 