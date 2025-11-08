import sqlite3
import hashlib
from datetime import datetime
from pwdlib import PasswordHash

def init_db():
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()

    query = '''
    CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    proficiency_level TEXT CHECK(proficiency_level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    certificate TEXT,
    join_date TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT CHECK(level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    title TEXT,
    description TEXT,
    duration_weeks INTEGER,
    course_plan TEXT
    );

    CREATE TABLE IF NOT EXISTS user_courses (
    user_id INTEGER,
    course_id INTEGER,
    start_date TEXT,
    progress_percent REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );

    CREATE TABLE IF NOT EXISTS modules (
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    week_number INTEGER,
    content_html TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );

    CREATE TABLE IF NOT EXISTS tests (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    test_html TEXT,
    submitted_answers_json TEXT,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    assessed BOOLEAN DEFAULT 0,
    assessed_level TEXT CHECK(assessed_level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    assessed_by_model TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

    CREATE TABLE IF NOT EXISTS module_ratings (
    module_id INTEGER,
    user_id INTEGER,
    course_id INTEGER,
    rating BOOLEAN DEFAULT 0,
    review TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );

    CREATE TABLE IF NOT EXISTS progress_tracking (
        module_attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        module_id INTEGER,
        course_id INTEGER,
        answers_json TEXT,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        assessed BOOLEAN DEFAULT 0,
        assessed_score REAL CHECK(assessed_score BETWEEN 0 AND 100),
        assessed_by_model TEXT,
        comments_from_model TEXT,
        phoenix_run_id TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (module_id) REFERENCES modules(module_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id)

    '''
    cursor.execute(query)
    connection.commit()

def create_user(name, surname, email, password):
    
    cursor = connection.cursor()
    password_hash = PasswordHash.recommended().hash(password)

    cursor.execute(
        "INSERT INTO users (name, surname, email, password_hash, email) VALUES (?, ?, ?, ?, ?)",
        (name, surname, email, password_hash, email)
    )
    connection.commit()
    
    return True, "User registered successfully."