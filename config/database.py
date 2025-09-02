import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

class FAQDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()
    
    def _ensure_database_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _create_tables(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS faqs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    frequency INTEGER DEFAULT 1
                )
            ''')
            conn.commit()
    
    def insert_faqs(self, faqs: List[Dict[str, str]]):
        with sqlite3.connect(self.db_path) as conn:
            for faq in faqs:
                # Check if similar question exists
                existing = conn.execute(
                    'SELECT id, frequency FROM faqs WHERE question = ?',
                    (faq['question'],)
                ).fetchone()
                
                if existing:
                    # Update frequency
                    conn.execute(
                        'UPDATE faqs SET frequency = frequency + 1 WHERE id = ?',
                        (existing[0],)
                    )
                else:
                    # Insert new FAQ
                    conn.execute(
                        'INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)',
                        (faq['question'], faq['answer'], faq.get('category', 'General'))
                    )
            conn.commit()
    
    def get_all_faqs(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT question, answer, category FROM faqs ORDER BY category, frequency DESC').fetchall()
            return [dict(row) for row in rows]