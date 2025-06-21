import sqlite3
import os

try:
    print(f"Database file exists: {os.path.exists('data/processed/recommendation.db')}")
    
    conn = sqlite3.connect('data/processed/recommendation.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables in database: {[table[0] for table in tables]}")
    
    if 'Items' in [table[0] for table in tables]:
        cursor.execute("PRAGMA table_info(Items);")
        columns = cursor.fetchall()
        print(f"Items table columns: {[column[1] for column in columns]}")
        
        cursor.execute("SELECT COUNT(*) FROM Items;")
        count = cursor.fetchone()[0]
        print(f"Number of movies in Items table: {count}")
        
        try:
            cursor.execute("SELECT item_id, title, language_code, language, region FROM Items LIMIT 5;")
            movies = cursor.fetchall()
            print("Sample movies with language info:")
            for movie in movies:
                print(f"  - {movie}")
        except sqlite3.OperationalError as e:
            print(f"Error querying language fields: {e}")
            
            # Try with different columns
            cursor.execute("SELECT * FROM Items LIMIT 1;")
            row = cursor.fetchone()
            columns = [description[0] for description in cursor.description]
            print(f"Available columns: {columns}")
    
    conn.close()
except Exception as e:
    print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database() 