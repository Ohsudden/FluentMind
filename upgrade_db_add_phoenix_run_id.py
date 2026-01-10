import sqlite3
import os

db_path = 'English_courses.db'

def upgrade_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if phoenix_run_id column exists
    cursor.execute("PRAGMA table_info(module)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'phoenix_run_id' not in columns:
        print("Adding phoenix_run_id to module table...")
        cursor.execute("ALTER TABLE module ADD COLUMN phoenix_run_id TEXT")
        conn.commit()
    else:
        print("phoenix_run_id already exists in module table.")
    
    conn.close()

if __name__ == "__main__":
    if os.path.exists(db_path):
        upgrade_db()
    else:
        print("Database not found.")
