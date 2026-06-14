import os
import json
import sqlite3
import time
import hashlib
from typing import Any, Optional, Dict

# Default TTL in seconds (24 hours)
DEFAULT_TTL = 86400

def get_db_connection():
    """Get a connection to the SQLite database."""
    db_path = os.environ.get('CACHE_DB_PATH', './cache.db')
    conn = sqlite3.connect(db_path)
    # Enable foreign keys and set row factory to dict-like
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database table if it doesn't exist."""
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS plan_cache (
                cache_key TEXT PRIMARY KEY,
                plan_json BLOB NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0,
                context_hash TEXT
            )
        ''')
        conn.commit()
    finally:
        conn.close()

def _normalize_query(query: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Normalize the query string and context to produce a consistent string for hashing.
    This is a helper function that can be used by the caller to generate the cache_key.
    The actual cache_key (SHA-256) should be computed outside and passed as plan_id.
    """
    if context is None:
        context = {}
    q = query.lower().strip()
    q = ' '.join(q.split())  # collapse whitespace
    # Optional: remove punctuation that does not affect meaning
    # q = ''.join(c for c in q if c.isalnum() or c.isspace())
    # Context: hour bucket (e.g., every 6 hours) to allow refresh
    hour_bucket = int(time.time() // 21600)  # 6-hour blocks
    context_str = f"|hour_bucket:{hour_bucket}"
    if context.get('user_id'):
        context_str += f"|user:{context['user_id']}"
    # Add any other context keys that are provided
    for key, value in context.items():
        if key not in ['user_id']:  # already handled
            context_str += f"|{key}:{value}"
    return q + context_str

def hash_key(normalized: str) -> str:
    """Compute SHA-256 hash of the normalized string."""
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def store_plan(plan_id: str, plan_obj: Any, ttl_seconds: int = DEFAULT_TTL) -> None:
    """
    Store a plan in the cache.
    :param plan_id: The cache key (SHA-256 hash of normalized query + context)
    :param plan_obj: The plan object (must be JSON serializable)
    :param ttl_seconds: Time to live in seconds (default: 24 hours)
    """
    init_db()
    conn = get_db_connection()
    try:
        plan_json = json.dumps(plan_obj).encode('utf-8')
        now = int(time.time())
        expires_at = now + ttl_seconds
        conn.execute('''
            INSERT OR REPLACE INTO plan_cache (cache_key, plan_json, created_at, expires_at, hit_count)
            VALUES (?, ?, ?, ?, 0)
        ''', (plan_id, plan_json, now, expires_at))
        conn.commit()
    finally:
        conn.close()

def load_plan(plan_id: str) -> Optional[Any]:
    """
    Load a plan from the cache if it exists and is not expired.
    :param plan_id: The cache key (SHA-256 hash of normalized query + context)
    :return: The plan object if found and valid, else None
    """
    init_db()
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            SELECT plan_json, expires_at, hit_count
            FROM plan_cache
            WHERE cache_key = ?
        ''', (plan_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        now = int(time.time())
        if now > row['expires_at']:
            # Entry has expired, delete it
            conn.execute('DELETE FROM plan_cache WHERE cache_key = ?', (plan_id,))
            conn.commit()
            return None
        # Update hit count
        conn.execute('''
            UPDATE plan_cache
            SET hit_count = hit_count + 1
            WHERE cache_key = ?
        ''', (plan_id,))
        conn.commit()
        # Deserialize the plan
        plan_json = row['plan_json']
        if isinstance(plan_json, bytes):
            plan_json = plan_json.decode('utf-8')
        return json.loads(plan_json)
    finally:
        conn.close()

def invalidate(plan_id: str) -> None:
    """
    Remove a plan from the cache.
    :param plan_id: The cache key to invalidate
    """
    init_db()
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM plan_cache WHERE cache_key = ?', (plan_id,))
        conn.commit()
    finally:
        conn.close()

# Initialize the database on module import
init_db()