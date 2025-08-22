
import sqlite3
import json
from datetime import datetime
from typing import List, Tuple, Optional

class ChatDatabase:
    def __init__(self):
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'dark',
                auto_summarize INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)
        ''')
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)
        ''')
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def create_conversation(self, user_id: int, title: str) -> int:
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
                (user_id, title)
            )
            conversation_id = c.lastrowid
            conn.commit()
            return conversation_id
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def add_message(self, conversation_id: int, role: str, content: str, metadata: dict = None) -> int:
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            c.execute(
                "INSERT INTO messages (conversation_id, role, content, metadata) VALUES (?, ?, ?, ?)",
                (conversation_id, role, content, metadata_json)
            )
            
            c.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,)
            )
            
            conn.commit()
            return c.lastrowid
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def get_user_conversations(self, user_id: int) -> List[Tuple]:
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                """SELECT id, title, created_at, updated_at 
                   FROM conversations 
                   WHERE user_id = ? 
                   ORDER BY updated_at DESC""",
                (user_id,)
            )
            return c.fetchall()
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def get_conversation_messages(self, conversation_id: int) -> List[Tuple]:
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                """SELECT role, content, timestamp, metadata 
                   FROM messages 
                   WHERE conversation_id = ? 
                   ORDER BY timestamp ASC""",
                (conversation_id,)
            )
            return c.fetchall()
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def delete_conversation(self, conversation_id: int):
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                "DELETE FROM conversations WHERE id = ?",
                (conversation_id,)
            )
            conn.commit()
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def update_conversation_title(self, conversation_id: int, new_title: str):
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (new_title, conversation_id)
            )
            conn.commit()
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def search_conversations(self, user_id: int, query: str) -> List[Tuple]:
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                """SELECT DISTINCT c.id, c.title, c.created_at, c.updated_at
                   FROM conversations c
                   JOIN messages m ON c.id = m.conversation_id
                   WHERE c.user_id = ? AND (c.title LIKE ? OR m.content LIKE ?)
                   ORDER BY c.updated_at DESC""",
                (user_id, f'%{query}%', f'%{query}%')
            )
            return c.fetchall()
        except Exception as e:
            raise e
        finally:
            conn.close()
    
    def get_user_preferences(self, user_id: int) -> dict:
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            c.execute(
                "SELECT theme, auto_summarize FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )
            result = c.fetchone()
            if result:
                return {"theme": result[0], "auto_summarize": bool(result[1])}
            else:
                # Create default preferences
                c.execute(
                    "INSERT INTO user_preferences (user_id) VALUES (?)",
                    (user_id,)
                )
                conn.commit()
                return {"theme": "dark", "auto_summarize": False}
        except Exception as e:
            return {"theme": "dark", "auto_summarize": False}
        finally:
            conn.close()
    
    def update_user_preferences(self, user_id: int, theme: str = None, auto_summarize: bool = None):
        conn = sqlite3.connect('chats.db')
        c = conn.cursor()
        
        try:
            if theme is not None and auto_summarize is not None:
                c.execute(
                    "UPDATE user_preferences SET theme = ?, auto_summarize = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (theme, int(auto_summarize), user_id)
                )
            elif theme is not None:
                c.execute(
                    "UPDATE user_preferences SET theme = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (theme, user_id)
                )
            elif auto_summarize is not None:
                c.execute(
                    "UPDATE user_preferences SET auto_summarize = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (int(auto_summarize), user_id)
                )
            
            conn.commit()
        except Exception as e:
            raise e
        finally:
            conn.close()