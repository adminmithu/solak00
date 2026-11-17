import sqlite3
import datetime
from typing import Optional, List, Dict, Any
from config import DB_PATH, ADMIN_ID

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                status TEXT DEFAULT 'pending',
                default_pass TEXT,
                pass_mode TEXT DEFAULT 'ask_each_time',
                created_at TEXT,
                approved_at TEXT
            )
        """)
        
        # Accounts table (Multilogin accounts created)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                password TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Support tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                admin_reply TEXT,
                status TEXT DEFAULT 'open',
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Used emails table (to strictly avoid repetitions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS used_emails (
                email TEXT PRIMARY KEY,
                created_at TEXT
            )
        """)
        
        conn.commit()

def register_or_get_user(user_id: int, username: Optional[str], first_name: Optional[str]) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_admin = (user_id == ADMIN_ID)
        
        if not row:
            # Auto-approve admin
            initial_status = 'approved' if is_admin else 'pending'
            cursor.execute("""
                INSERT INTO users (user_id, username, first_name, status, created_at, approved_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username or '', first_name or '', initial_status, now_str, now_str if is_admin else None))
            conn.commit()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())
        else:
            # Update username/first_name if changed
            cursor.execute("""
                UPDATE users SET username = ?, first_name = ? WHERE user_id = ?
            """, (username or '', first_name or '', user_id))
            if is_admin and row['status'] != 'approved':
                cursor.execute("UPDATE users SET status = 'approved' WHERE user_id = ?", (user_id,))
            conn.commit()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def approve_user(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE users SET status = 'approved', approved_at = ? WHERE user_id = ?
        """, (now_str, user_id))
        conn.commit()
        return cursor.rowcount > 0

def reject_user(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET status = 'rejected' WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        return cursor.rowcount > 0

def block_user(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET status = 'blocked' WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_pending_users() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE status = 'pending' ORDER BY created_at DESC")
        return [dict(r) for r in cursor.fetchall()]

def get_approved_users() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE status = 'approved' ORDER BY approved_at DESC")
        return [dict(r) for r in cursor.fetchall()]

def set_user_password(user_id: int, password: str, mode: str = "permanent") -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET default_pass = ?, pass_mode = ? WHERE user_id = ?
        """, (password, mode, user_id))
        conn.commit()
        return cursor.rowcount > 0

def clear_user_password(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET default_pass = NULL, pass_mode = 'ask_each_time' WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        return cursor.rowcount > 0

def add_account(user_id: int, email: str, password: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO accounts (user_id, email, password, status, created_at)
            VALUES (?, ?, ?, 'active', ?)
        """, (user_id, email, password, now_str))
        conn.commit()
        return cursor.lastrowid

def get_user_accounts_count(user_id: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM accounts WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row['cnt'] if row else 0

def get_user_accounts(user_id: int, limit: int = 5, offset: int = 0) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM accounts 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
        return [dict(r) for r in cursor.fetchall()]

def get_user_all_accounts(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM accounts 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]

def get_all_accounts(limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, u.username 
            FROM accounts a 
            LEFT JOIN users u ON a.user_id = u.user_id 
            ORDER BY a.created_at DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

def get_stats() -> Dict[str, int]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute("SELECT COUNT(*) as approved_users FROM users WHERE status = 'approved'")
        approved_users = cursor.fetchone()['approved_users']
        
        cursor.execute("SELECT COUNT(*) as pending_users FROM users WHERE status = 'pending'")
        pending_users = cursor.fetchone()['pending_users']
        
        cursor.execute("SELECT COUNT(*) as total_accounts FROM accounts")
        total_accounts = cursor.fetchone()['total_accounts']
        
        return {
            "total_users": total_users,
            "approved_users": approved_users,
            "pending_users": pending_users,
            "total_accounts": total_accounts
        }

def save_support_ticket(user_id: int, message: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO support_tickets (user_id, message, status, created_at)
            VALUES (?, ?, 'open', ?)
        """, (user_id, message, now_str))
        conn.commit()
        return cursor.lastrowid

def get_support_ticket(ticket_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def reply_support_ticket(ticket_id: int, reply: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE support_tickets SET admin_reply = ?, status = 'replied' WHERE id = ?
        """, (reply, ticket_id))
        conn.commit()
        return cursor.rowcount > 0

def is_email_used(email: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM used_emails WHERE email = ?", (email,))
        if cursor.fetchone():
            return True
        cursor.execute("SELECT 1 FROM accounts WHERE email = ?", (email,))
        return bool(cursor.fetchone())

def is_user_approved(user_id: int) -> bool:
    """Checks if a user is approved to use any bot features"""
    if user_id == ADMIN_ID:
        return True
    user = get_user(user_id)
    return bool(user and user.get("status") == "approved")

def mark_email_used(email: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT OR IGNORE INTO used_emails (email, created_at)
            VALUES (?, ?)
        """, (email, now_str))
        conn.commit()
