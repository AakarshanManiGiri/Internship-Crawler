import sqlite3
from typing import List, Optional, Dict
from models.internship import Internship
from datetime import datetime, timedelta

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
    
    def get_internships_with_filters(self, country: Optional[str] = None, date_filter: Optional[str] = None) -> List[Internship]:
        """Get internships with optional filtering by country and date range
        
        Args:
            country: Filter by location/country (case-insensitive)
            date_filter: Filter by date range ('past_hour', 'past_week', 'past_month')
        
        Returns:
            List of filtered internships
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM internships WHERE 1=1"
        params = []
        
        # Add country filter
        if country:
            query += " AND location LIKE ?"
            params.append(f"%{country}%")
        
        # Add date filter
        if date_filter:
            now = datetime.now()
            if date_filter == 'past_hour':
                cutoff_date = now - timedelta(hours=1)
            elif date_filter == 'past_week':
                cutoff_date = now - timedelta(weeks=1)
            elif date_filter == 'past_month':
                cutoff_date = now - timedelta(days=30)
            else:
                cutoff_date = None
            
            if cutoff_date:
                query += " AND datetime(posted_date) >= ?"
                params.append(cutoff_date.isoformat())
        
        # Sort by posted_date descending (newest first)
        query += " ORDER BY datetime(posted_date) DESC"
        
        cursor.execute(query, params)
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


