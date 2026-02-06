"""
User authentication and management module.
Handles user login, logout, and user data management using SQLite.
"""
import sqlite3
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, List


class AuthManager:
    """Manages user authentication and user data."""
    
    def __init__(self, db_path: str = "data/users.db"):
        """Initialize the authentication manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._ensure_admin()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def _ensure_admin(self):
        """Ensure an admin user exists."""
        admin_user = os.getenv("ADMIN_USER", "admin")
        admin_pass = os.getenv("ADMIN_PASS", "admin123")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (admin_user,))
        if cursor.fetchone() is None:
            password_hash = self._hash_password(admin_pass)
            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, 1)",
                (admin_user, password_hash)
            )
            conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256.
        
        Args:
            password: Plain text password
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User dict if authentication successful, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, is_admin FROM users WHERE username = ? AND password_hash = ? AND is_active = 1",
            (username, self._hash_password(password))
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "is_admin": bool(row[2])
            }
        return None
    
    def create_user(self, username: str, password: str, is_admin: bool = False) -> bool:
        """Create a new user.
        
        Args:
            username: Username
            password: Plain text password
            is_admin: Whether the user is an admin
            
        Returns:
            True if user created successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            password_hash = self._hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, password_hash, 1 if is_admin else 0)
            )
            conn.commit()
            conn.close()
            
            # Create user data directory
            user_id = self.get_user_id(username)
            if user_id:
                Path(f"data/{user_id}").mkdir(parents=True, exist_ok=True)
            
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user_id(self, username: str) -> Optional[int]:
        """Get user ID by username.
        
        Args:
            username: Username
            
        Returns:
            User ID if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def list_users(self) -> List[Dict]:
        """List all users.
        
        Returns:
            List of user dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, is_admin, is_active FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "user_id": row[0],
                "username": row[1],
                "is_admin": bool(row[2]),
                "is_active": bool(row[3])
            }
            for row in rows
        ]
    
    def toggle_user_status(self, username: str) -> bool:
        """Toggle user active status.
        
        Args:
            username: Username
            
        Returns:
            True if status toggled successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 1 - is_active WHERE username = ?",
                (username,)
            )
            conn.commit()
            conn.close()
            return True
        except:
            return False
