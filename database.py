import sqlite3
import hashlib
import json
from datetime import datetime
from pwdlib import PasswordHash

class Database:
    def __init__(self, db_name='English_courses.db'):
        self.db_name = db_name

    def init_db(self):
        connection = sqlite3.connect(self.db_name)
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

    def create_user(self, name, surname, email, password):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        password_hash = PasswordHash.recommended().hash(password)

        try:
            cursor.execute(
                "INSERT INTO user (name, surname, email, password_hash) VALUES (?, ?, ?, ?)",
                (name, surname, email, password_hash)
            )
            connection.commit()
            return True, "User registered successfully."
        except sqlite3.IntegrityError:
            return False, "Email already exists."
        finally:
            connection.close()
        
    def login_user(self, email, password):
        connection = sqlite3.connect(self.db_name)
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

    def get_user_id_by_email(self, email: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM user WHERE email = ?", (email,))
        row = cursor.fetchone()
        connection.close()
        if row:
            return row[0]
        return None

    def get_user_by_id(self, user_id: int):
        connection = sqlite3.connect(self.db_name)
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
        
    def rechange_password(self, user_id: int, new_password: str):
        new_password_hash = PasswordHash.recommended().hash(new_password)
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET password_hash = ? WHERE user_id = ?",
            (new_password_hash, user_id)
        )
        connection.commit()
        connection.close()

    def upload_certificate(self, user_id: int, certificate: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO certificate (user_id, certificate) VALUES (?, ?)" ,
            (user_id, certificate)
        )
        connection.commit()
        connection.close()

    def upload_image(self, user_id: int, image_data: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET pp_image = ? WHERE user_id = ?",
            (image_data, user_id)
        )
        connection.commit()
        connection.close()


    def get_vocabulary_by_user(self, user_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT words FROM vocabulary WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        connection.close()

        if not row or row[0] is None:
            return {}

        try:
            data = json.loads(row[0])
        except json.JSONDecodeError:
            return {}

        if isinstance(data, dict):
            return data

        return {}


    def save_vocabulary_by_user(self, user_id: int, words: dict):
        serialized = json.dumps(words, ensure_ascii=False)
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT vocabulary_id FROM vocabulary WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()

        if row:
            cursor.execute(
                "UPDATE vocabulary SET words = ? WHERE vocabulary_id = ?",
                (serialized, row[0])
            )
        else:
            cursor.execute(
                "INSERT INTO vocabulary (user_id, words) VALUES (?, ?)",
                (user_id, serialized)
            )

        connection.commit()
        connection.close()

    def update_native_language(self, user_id: int, native_language: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET native_language = ? WHERE user_id = ?",
            (native_language, user_id)
        )
        connection.commit()
        connection.close()

    def update_interface_language(self, user_id: int, interface_language: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET interface_language = ? WHERE user_id = ?",
            (interface_language, user_id)
        )
        connection.commit()
        connection.close()

    def update_email(self, user_id: int, email: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET email = ? WHERE user_id = ?",
            (email, user_id)
        )
        connection.commit()
        connection.close()


    def add_test(self, user_id: int, test_html: str, submitted_answers_json: str, assessed: bool,
                    assessed_level: str, assessed_by_model: str, phoenix_run_id: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO test (user_id, test_html, submitted_answers_json, assessed, assessed_level, assessed_by_model, phoenix_run_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, test_html, submitted_answers_json, assessed, assessed_level, assessed_by_model, phoenix_run_id)
        )
        connection.commit()
        connection.close()
    
    def add_progress_tracking(self, user_id: int, module_id: int, course_id: int, answers_json: str, assessed: bool,
                    assessed_score: float, assessed_by_model: str, comments_from_model: str, phoenix_run_id: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO progress_tracking (user_id, module_id, course_id, answers_json, assessed, assessed_score, assessed_by_model, comments_from_model, phoenix_run_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, module_id, course_id, answers_json, assessed, assessed_score, assessed_by_model, comments_from_model, phoenix_run_id)
        )
        connection.commit()
        connection.close()
    
    def add_course(self, level: str, title: str, description: str, duration_weeks: int, course_plan: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO course (level, title, description, duration_weeks, course_plan) VALUES (?, ?, ?, ?, ?)",
            (level, title, description, duration_weeks, course_plan)
        )
        course_id = cursor.lastrowid
        connection.commit()
        connection.close()
        return course_id
    
    def enroll_user_in_course(self, user_id: int, course_id: int, start_date: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO user_course (user_id, course_id, start_date) VALUES (?, ?, ?)",
            (user_id, course_id, start_date)
        )
        connection.commit()
        connection.close()

    def add_module(self, course_id: int, title: str, week_number: int, content_html: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO module (course_id, title, week_number, content_html) VALUES (?, ?, ?, ?)",
            (course_id, title, week_number, content_html)
        )
        connection.commit()
        connection.close()

    def rate_module(self, module_id: int, user_id: int, course_id: int, rating: bool, review: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO module_rating (module_id, user_id, course_id, rating, review) VALUES (?, ?, ?, ?, ?)",
            (module_id, user_id, course_id, rating, review)
        )
        connection.commit()
        connection.close()

    def create_pending_test(self, user_id: int, test_html: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO test (user_id, test_html) VALUES (?, ?)",
            (user_id, test_html)
        )
        test_id = cursor.lastrowid
        connection.commit()
        connection.close()
        return test_id

    def get_test(self, test_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT test_id, user_id, test_html, submitted_answers_json FROM test WHERE test_id = ?",
            (test_id,)
        )
        row = cursor.fetchone()
        connection.close()
        if not row:
            return None
        return {
            "test_id": row[0],
            "user_id": row[1],
            "test_html": row[2],
            "submitted_answers_json": row[3]
        }

    def update_test_submission(self, test_id: int, submitted_answers_json: str, assessed_level: str, assessed_by_model: str, phoenix_run_id: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE test SET submitted_answers_json = ?, assessed = 1, assessed_level = ?, assessed_by_model = ?, phoenix_run_id = ?, submitted_at = CURRENT_TIMESTAMP WHERE test_id = ?",
            (submitted_answers_json, assessed_level, assessed_by_model, phoenix_run_id, test_id)
        )
        connection.commit()
        connection.close()
    
    def update_english_level(self, user_id: int, new_level: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE user SET proficiency_level = ? WHERE user_id = ?",
            (new_level, user_id)
        )
        connection.commit()
        connection.close()
    
    def get_user_courses(self, user_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            '''
            SELECT c.course_id, c.level, c.title, c.description, c.duration_weeks, c.course_plan
            FROM course c
            JOIN user_course uc ON c.course_id = uc.course_id
            WHERE uc.user_id = ?
            ''',
            (user_id,)
        )
        rows = cursor.fetchall()
        connection.close()
        courses = []
        for row in rows:
            courses.append({
                "course_id": row[0],
                "level": row[1],
                "title": row[2],
                "description": row[3],
                "duration_weeks": row[4],
                "course_plan": row[5]
            })
        return courses
    
    def add_user_to_course(self, user_id: int, course_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO user_course (user_id, course_id, start_date) VALUES (?, ?, ?)",
            (user_id, course_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        connection.commit()
        connection.close()

    def get_course_by_id(self, course_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT course_id, level, title, description, duration_weeks, course_plan FROM course WHERE course_id = ?",
            (course_id,)
        )
        row = cursor.fetchone()
        connection.close()
        if not row:
            return None
        return {
            "course_id": row[0],
            "level": row[1],
            "title": row[2],
            "description": row[3],
            "duration_weeks": row[4],
            "course_plan": row[5]
        }
    def get_modules_by_course(self, course_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT module_id, course_id, title, week_number, content_html FROM module WHERE course_id = ? ORDER BY week_number",
            (course_id,)
        )
        rows = cursor.fetchall()
        connection.close()
        modules = []
        for row in rows:
            modules.append({
                "module_id": row[0],
                "course_id": row[1],
                "title": row[2],
                "week_number": row[3],
                "content_html": row[4]
            })
        return modules
    def get_module_content(self, module_id: int, course_id: int):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT content_html FROM module WHERE module_id = ? AND course_id = ?",
            (module_id, course_id)
        )
        row = cursor.fetchone()
        connection.close()
        if not row:
            return None
        return row[0]
    
    def assess_module_user(self, user_id: int, module_id: int, course_id: int, rating: bool, review: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO module_rating (module_id, user_id, course_id, rating, review) VALUES (?, ?, ?, ?, ?)",
            (module_id, user_id, course_id, rating, review)
        )
        connection.commit()
        connection.close()