# init_db.py
from asyncio.windows_events import NULL
import sqlite3
import os

def init_db():
    db_path = "/home/pi/diplearning_local.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            option4 TEXT NOT NULL,
            correct_option INTEGER NOT NULL,
            explanation TEXT NOT NULL
        )
    """)

    # Bootstrap
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Super admin
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("superadmin", "password", "super_admin"))
        # Exemples
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("prof1", "prof123", "prof"))
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("eleve1", NULL, "eleve"))
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("eleve2", NULL, "eleve"))
        
        conn.commit()
        print("Utilisateurs créés :")
        print("- superadmin/password (super_admin)")
        print("- prof1/prof123 (prof)") 
        print("- eleve1, eleve2 (élèves)")

    conn.close()

if __name__ == "__main__":
    init_db()