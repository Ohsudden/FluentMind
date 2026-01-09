import sqlite3
import os

db_path = 'English_courses.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM module')
    modules = cursor.fetchall()
    print(f"Total modules: {len(modules)}")
    for m in modules:
        print(m)
    conn.close()
