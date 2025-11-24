import sqlite3
from typing import List, Optional, Dict
from models.internship import Internship
from datetime import datetime

class Database:
    def __init__(self, db_path: str = "internships.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                url TEXT UNIQUE NOT NULL,
                posted_date TEXT,
                description TEXT,
                requirements TEXT,
                created_at TEXT,
                notified BOOLEAN DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                preferences TEXT,
                created_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_internship(self, internship: Internship) -> Optional[int]:
        """Save new internship if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO internships 
                (company, title, location, url, posted_date, description, requirements, created_at, notified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                internship.company,
                internship.title,
                internship.location,
                internship.url,
                internship.posted_date.isoformat(),
                internship.description,
                ','.join(internship.requirements),
                internship.created_at.isoformat(),
                internship.notified
            ))
            
            conn.commit()
            return cursor.lastrowid
        
        except sqlite3.IntegrityError:
            # Internship already exists
            return None
        
        finally:
            conn.close()
    
    def get_unnotified_internships(self) -> List[Internship]:
        """Get all internships that haven't been notified"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM internships WHERE notified = 0
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        internships = []
        for row in rows:
            internships.append(Internship(
                id=row[0],
                company=row[1],
                title=row[2],
                location=row[3],
                url=row[4],
                posted_date=datetime.fromisoformat(row[5]),
                description=row[6],
                requirements=row[7].split(',') if row[7] else [],
                created_at=datetime.fromisoformat(row[8]),
                notified=bool(row[9])
            ))
        
        return internships
    
    def mark_as_notified(self, internship_ids: List[int]):
        """Mark internships as notified"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            UPDATE internships 
            SET notified = 1 
            WHERE id IN ({','.join(['?'] * len(internship_ids))})
        """, internship_ids)
        
        conn.commit()
        conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """Get all registered users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': row[0], 'email': row[1], 'preferences': row[2]} for row in rows]


