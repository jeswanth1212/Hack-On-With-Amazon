import sqlite3
import os
import argparse

# Database path
DB_PATH = 'data/processed/recommendation.db'

def execute_query(query):
    """Execute a SQL query and print results."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Print column headers
        if columns:
            print(" | ".join(columns))
            print("-" * (sum(len(col) + 3 for col in columns) - 1))
        
        # Fetch and print data
        rows = cursor.fetchall()
        for row in rows:
            # Convert None values to "NULL"
            formatted_row = [str(val) if val is not None else "NULL" for val in row]
            print(" | ".join(formatted_row))
        
        print(f"\n{len(rows)} rows returned")
        
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
    finally:
        if conn:
            conn.close()

def show_tables():
    """Show all tables in the database."""
    execute_query("SELECT name FROM sqlite_master WHERE type='table'")

def count_rows(table_name):
    """Count rows in a table."""
    execute_query(f"SELECT COUNT(*) as row_count FROM {table_name}")

def show_schema(table_name):
    """Show schema for a table."""
    execute_query(f"PRAGMA table_info({table_name})")

def show_sample(table_name, limit=5):
    """Show sample data from a table."""
    execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query SQLite database")
    parser.add_argument("--query", "-q", help="SQL query to execute")
    parser.add_argument("--tables", "-t", action="store_true", help="Show all tables")
    parser.add_argument("--count", "-c", help="Count rows in table")
    parser.add_argument("--schema", "-s", help="Show schema for table")
    parser.add_argument("--sample", help="Show sample data from table")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Limit for sample query")
    
    args = parser.parse_args()
    
    if args.query:
        execute_query(args.query)
    elif args.tables:
        show_tables()
    elif args.count:
        count_rows(args.count)
    elif args.schema:
        show_schema(args.schema)
    elif args.sample:
        show_sample(args.sample, args.limit)
    else:
        print("Please specify a command. Use --help for options.") 