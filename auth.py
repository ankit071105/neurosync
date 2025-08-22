
import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import jwt
import bcrypt
from typing import Optional, Tuple

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(username: str, password: str, email: str, full_name: str = "") -> Tuple[bool, str]:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        hashed_pw = hash_password(password)
        c.execute(
            "INSERT INTO users (username, password_hash, email, full_name) VALUES (?, ?, ?, ?)",
            (username, hashed_pw, email, full_name)
        )
        conn.commit()
        return True, "User registered successfully!"
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if "username" in error_msg:
            return False, "Username already exists"
        elif "email" in error_msg:
            return False, "Email already exists"
        else:
            return False, "Registration failed"
    except Exception as e:
        return False, f"Registration error: {str(e)}"
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Tuple[bool, Optional[int], str]:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,)
        )
        user = c.fetchone()
        
        if not user:
            return False, None, "User not found"
        
        user_id, hashed_pw = user
        if verify_password(password, hashed_pw):
       
            c.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            conn.commit()
            return True, user_id, "Login successful"
        else:
            return False, None, "Invalid password"
    except Exception as e:
        return False, None, f"Authentication error: {str(e)}"
    finally:
        conn.close()


def create_session_token(user_id: int) -> str:

    token = hashlib.sha256(f"{user_id}{datetime.now()}{os.urandom(16)}".encode()).hexdigest()
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    expires_at = datetime.now() + timedelta(days=7)  
    c.execute(
        "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at)
    )
    
    conn.commit()
    conn.close()
    
    return token
def verify_session_token(token: str) -> Optional[int]:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute(
            "SELECT user_id FROM user_sessions WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP",
            (token,)
        )
        session = c.fetchone()
        return session[0] if session else None
    except:
        return None
    finally:
        conn.close()


def get_user_info(user_id: int) -> Optional[Tuple]:
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute(
            "SELECT id, username, email, full_name, created_at, last_login FROM users WHERE id = ?",
            (user_id,)
        )
        return c.fetchone()
    except:
        return None
    finally:
        conn.close()


def logout_user(token: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute(
            "DELETE FROM user_sessions WHERE session_token = ?",
            (token,)
        )
        conn.commit()
    finally:
        conn.close()