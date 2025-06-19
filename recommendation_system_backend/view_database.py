import sqlite3
import pandas as pd
from tabulate import tabulate
import os
import argparse

# Database path
DB_PATH = 'data/processed/recommendation.db'

def view_table(table_name=None, limit=5):
    """View a specific table or list all tables."""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return
    
    print(f"Connecting to database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    available_tables = [t[0] for t in cursor.fetchall()]
    
    if not available_tables:
        print("No tables found in the database.")
        conn.close()
        return
    
    print(f"\nAvailable tables: {', '.join(available_tables)}")
    
    # If no specific table requested, show summary of all tables
    if table_name is None:
        print("\n=== Database Summary ===")
        for t in available_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            print(f"{t}: {count} rows")
        
        print("\nUse --table [TABLE_NAME] to view details of a specific table")
        conn.close()
        return
    
    # Check if requested table exists
    if table_name not in available_tables:
        print(f"Table '{table_name}' not found. Available tables: {', '.join(available_tables)}")
        conn.close()
        return
    
    # Show table schema
    print(f"\n=== Table: {table_name} ===\n")
    schema_df = pd.read_sql_query(f"PRAGMA table_info({table_name})", conn)
    print("Schema:")
    schema_data = schema_df.values.tolist()
    headers = schema_df.columns.tolist()
    print(tabulate(schema_data, headers=headers, tablefmt="grid"))
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\nTotal rows: {count}")
    
    # Show sample data
    if count > 0:
        print(f"\nSample data (first {limit} rows):")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
            print(tabulate(df, headers='keys', tablefmt="grid", maxcolwidths=30, showindex=False))
        except Exception as e:
            print(f"Error displaying data: {e}")
    
    conn.close()

def monitor_table(table_name, interval=5, limit=5):
    """Monitor a table for changes at specified interval."""
    import time
    
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return
    
    print(f"Monitoring table '{table_name}' (press Ctrl+C to stop)...")
    
    try:
        last_count = None
        while True:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get current row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            current_count = cursor.fetchone()[0]
            
            # Get latest entries
            try:
                df = pd.read_sql_query(
                    f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT {limit}", 
                    conn
                )
                
                # Check if count has changed
                if last_count is not None and current_count != last_count:
                    diff = current_count - last_count
                    print(f"\n[{time.strftime('%H:%M:%S')}] {abs(diff)} {'new' if diff > 0 else 'deleted'} rows detected")
                    print(f"Current count: {current_count} rows")
                    print("Latest entries:")
                    print(tabulate(df, headers='keys', tablefmt="grid", maxcolwidths=30, showindex=False))
                elif last_count is None:
                    # First run
                    print(f"Initial count: {current_count} rows")
            except Exception as e:
                print(f"Error reading data: {e}")
            
            last_count = current_count
            conn.close()
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View SQLite database tables")
    parser.add_argument("--table", "-t", help="Specific table to view")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Number of rows to display")
    parser.add_argument("--monitor", "-m", action="store_true", help="Monitor table for changes")
    parser.add_argument("--interval", "-i", type=int, default=5, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    if args.monitor and args.table:
        monitor_table(args.table, args.interval, args.limit)
    else:
        view_table(args.table, args.limit) 