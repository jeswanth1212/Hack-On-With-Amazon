import sqlite3
import os
import time
import argparse
from datetime import datetime

# Database path
DB_PATH = 'data/processed/recommendation.db'

def get_table_info():
    """Get information about all tables in the database."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return {}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info = {}
        for table in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Get last record (if any)
            if count > 0:
                if table == 'Interactions':
                    cursor.execute(f"SELECT interaction_id, user_id, item_id, timestamp, sentiment_score, mood FROM {table} ORDER BY interaction_id DESC LIMIT 1")
                elif table == 'Items':
                    cursor.execute(f"SELECT item_id, title, genres, release_year FROM {table} ORDER BY rowid DESC LIMIT 1")
                else:
                    cursor.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 1")
                last_record = cursor.fetchone()
            else:
                last_record = None
            
            table_info[table] = {
                'count': count,
                'last_record': last_record
            }
        
        conn.close()
        return table_info
        
    except sqlite3.Error as e:
        print(f"Error getting table info: {e}")
        return {}

def monitor_database(interval=5):
    """Monitor the database for changes."""
    print(f"Monitoring database at {DB_PATH}")
    print(f"Checking for changes every {interval} seconds...")
    print("Press Ctrl+C to stop monitoring\n")
    
    previous_info = get_table_info()
    
    try:
        while True:
            current_info = get_table_info()
            changes_detected = False
            
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for changes...")
            
            for table, info in current_info.items():
                current_count = info['count']
                
                if table in previous_info:
                    previous_count = previous_info[table]['count']
                    diff = current_count - previous_count
                    
                    if diff != 0:
                        changes_detected = True
                        print(f"  Table '{table}': {abs(diff)} {'new' if diff > 0 else 'deleted'} records (now: {current_count})")
                        
                        # Show last record for additions
                        if diff > 0 and info['last_record']:
                            print(f"  Last record: {info['last_record']}")
                else:
                    # New table
                    changes_detected = True
                    print(f"  New table '{table}' with {current_count} records")
            
            if not changes_detected:
                print("  No changes detected")
            
            previous_info = current_info
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def add_test_data():
    """Add some test data to demonstrate database updates."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Add a test user if UserProfiles is empty
        cursor.execute("SELECT COUNT(*) FROM UserProfiles")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO UserProfiles (user_id, age, age_group, location)
            VALUES ('test_user', 25, 'young_adult', 'test_location')
            """)
            print("Added test user")
        
        # Add a test interaction
        cursor.execute("""
        INSERT INTO Interactions 
        (user_id, item_id, sentiment_score, mood, time_of_day, day_of_week)
        VALUES ('test_user', 'ml_1', 0.9, 'happy', 'evening', 'Monday')
        """)
        
        conn.commit()
        conn.close()
        print("Added test interaction")
        
    except sqlite3.Error as e:
        print(f"Error adding test data: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor SQLite database for changes")
    parser.add_argument("--interval", "-i", type=int, default=5, help="Monitoring interval in seconds")
    parser.add_argument("--add-test-data", "-t", action="store_true", help="Add test data to demonstrate updates")
    
    args = parser.parse_args()
    
    if args.add_test_data:
        add_test_data()
    
    monitor_database(args.interval) 