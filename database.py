import sqlite3
import hashlib
from datetime import datetime
from pwdlib import PasswordHash

def init_db():
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    surname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    proficiency_level TEXT CHECK(proficiency_level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    pp_image TEXT default 'img/settings/avatar-outline.svg',
    native_language TEXT,
    interface_language TEXT,
    join_date TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS course (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT CHECK(level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    title TEXT,
    description TEXT,
    duration_weeks INTEGER,
    course_plan TEXT
    );

    CREATE TABLE IF NOT EXISTS user_course (
    user_id INTEGER,
    course_id INTEGER,
    start_date TEXT,
    progress_percent REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
    );

    CREATE TABLE IF NOT EXISTS module (
    module_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    title TEXT,
    week_number INTEGER,
    content_html TEXT,
    FOREIGN KEY (course_id) REFERENCES course(course_id)
    );

    CREATE TABLE IF NOT EXISTS test (
    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    test_html TEXT,
    submitted_answers_json TEXT,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    assessed BOOLEAN DEFAULT 0,
    assessed_level TEXT CHECK(assessed_level IN ('A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    assessed_by_model TEXT,
    phoenix_run_id TEXT,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
    );

    CREATE TABLE IF NOT EXISTS module_rating (
    module_id INTEGER,
    user_id INTEGER,
    course_id INTEGER,
    rating BOOLEAN DEFAULT 0,
    review TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES module(module_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id)
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
        FOREIGN KEY (user_id) REFERENCES user(user_id),
        FOREIGN KEY (module_id) REFERENCES module(module_id),
        FOREIGN KEY (course_id) REFERENCES course(course_id)
    );
    CREATE TABLE IF NOT EXISTS certificate (
    certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        certificate TEXT,
        status BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES user(user_id)
    );
    CREATE TABLE IF NOT EXISTS vocabulary (
        vocabulary_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        words TEXT,
        FOREIGN KEY (user_id) REFERENCES user(user_id)
    );
    ''')
    connection.commit()
    connection.close()

def create_user(name, surname, email, password):
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()
    password_hash = PasswordHash.recommended().hash(password)

    cursor.execute(
        "INSERT INTO user (name, surname, email, password_hash) VALUES (?, ?, ?, ?)",
        (name, surname, email, password_hash)
    )
    connection.commit()
    connection.close()
    
    return True, "User registered successfully."

def login_user(email, password):
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()

    cursor.execute(
        "SELECT user_id, name, surname, email, password_hash FROM user WHERE email = ?",
        (email,)
    )
    row = cursor.fetchone()
    connection.close()

    if not row:
        return False, "User not found."

    stored_hash = row[4]
    if not PasswordHash.recommended().verify(password, stored_hash):
        return False, "Incorrect password."

    return True, {
        "id": row[0],
        "name": row[1],
        "surname": row[2],
        "email": row[3]
    }


def get_user_id_by_email(email: str):
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM user WHERE email = ?", (email,))
    row = cursor.fetchone()
    connection.close()
    if row:
        return row[0]
    return None


def get_user_by_id(user_id: int):
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()
    cursor.execute(
        "SELECT user_id, name, surname, email, password_hash, native_language, interface_language, proficiency_level, pp_image FROM user WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    connection.close()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "surname": row[2],
        "email": row[3],
        "password_hash": row[4],
        "native_language": row[5],
        "interface_language": row[6],
        "proficiency_level": row[7],
        "pp_image": row[8]
    }
    
def rechange_password(user_id: int, new_password: str):
    new_password_hash = PasswordHash.recommended().hash(new_password)
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE user SET password_hash = ? WHERE user_id = ?",
        (new_password_hash, user_id)
    )
    connection.commit()
    connection.close()

def upload_certificate(user_id: int, certificate: str):
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO certificate (user_id, certificate) VALUES (?, ?)" ,
        (user_id, certificate)
    )
    connection.commit()
    connection.close()

def upload_image(user_id: int, image_data: str):
    connection = sqlite3.connect('English_courses.db')
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE user SET pp_image = ? WHERE user_id = ?",
        (image_data, user_id)
    )
    connection.commit()
    connection.close()