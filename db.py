"""
SQLite 持久化存储
保存搜索结果、笔记和评论到本地数据库
"""

import os
import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime

DB_DIR = Path(__file__).resolve().parent / "output"
DB_PATH = DB_DIR / "toolbox.db"


def get_conn():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS search_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            sort_type TEXT DEFAULT 'general',
            time_range TEXT DEFAULT 'all',
            total_notes INTEGER DEFAULT 0,
            search_time TEXT,
            source_json_path TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES search_sessions(id),
            note_id TEXT NOT NULL,
            title TEXT DEFAULT '',
            desc TEXT DEFAULT '',
            note_type TEXT DEFAULT '',
            user_id TEXT DEFAULT '',
            nickname TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            home_url TEXT DEFAULT '',
            liked_count INTEGER DEFAULT 0,
            collected_count INTEGER DEFAULT 0,
            comment_count INTEGER DEFAULT 0,
            share_count INTEGER DEFAULT 0,
            tags TEXT DEFAULT '[]',
            upload_time TEXT DEFAULT '',
            ip_location TEXT DEFAULT '',
            image_list TEXT DEFAULT '[]',
            video_cover TEXT DEFAULT '',
            video_addr TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note_db_id INTEGER REFERENCES notes(id),
            note_id TEXT DEFAULT '',
            comment_id TEXT DEFAULT '',
            user_id TEXT DEFAULT '',
            nickname TEXT DEFAULT '',
            avatar TEXT DEFAULT '',
            content TEXT DEFAULT '',
            like_count INTEGER DEFAULT 0,
            ip_location TEXT DEFAULT '',
            upload_time TEXT DEFAULT '',
            pictures TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE INDEX IF NOT EXISTS idx_notes_session ON notes(session_id);
        CREATE INDEX IF NOT EXISTS idx_notes_keyword ON notes(nickname);
        CREATE INDEX IF NOT EXISTS idx_comments_note ON comments(note_db_id);
    """)
    conn.commit()
    conn.close()


def save_search_session(keyword, data, source_json_path=""):
    """保存一次搜索的所有结果"""
    init_db()
    conn = get_conn()
    try:
        results = data.get("results", [])
        search_time = data.get("search_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        cur = conn.execute(
            "INSERT INTO search_sessions (keyword, total_notes, search_time, source_json_path) VALUES (?,?,?,?)",
            (keyword, len(results), search_time, source_json_path),
        )
        session_id = cur.lastrowid

        for item in results:
            note = item.get("note", {})
            note_id = note.get("note_id", "")
            comments = item.get("comments", [])

            conn.execute(
                """INSERT INTO notes
                (session_id, note_id, title, desc, note_type, user_id, nickname, avatar, home_url,
                 liked_count, collected_count, comment_count, share_count,
                 tags, upload_time, ip_location, image_list, video_cover, video_addr)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    session_id,
                    note_id,
                    note.get("title", ""),
                    note.get("desc", ""),
                    note.get("note_type", ""),
                    note.get("user_id", ""),
                    note.get("nickname", ""),
                    note.get("avatar", ""),
                    note.get("home_url", ""),
                    int(note.get("liked_count") or 0),
                    int(note.get("collected_count") or 0),
                    int(note.get("comment_count") or 0),
                    int(note.get("share_count") or 0),
                    json.dumps(note.get("tags", []), ensure_ascii=False),
                    note.get("upload_time", ""),
                    note.get("ip_location", ""),
                    json.dumps(note.get("image_list", []), ensure_ascii=False),
                    note.get("video_cover", ""),
                    note.get("video_addr", ""),
                ),
            )
            note_db_id = cur.lastrowid

            for c in comments:
                conn.execute(
                    """INSERT INTO comments
                    (note_db_id, note_id, comment_id, user_id, nickname, avatar,
                     content, like_count, ip_location, upload_time, pictures)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        note_db_id,
                        note_id,
                        c.get("comment_id", ""),
                        c.get("user_id", ""),
                        c.get("nickname", ""),
                        c.get("avatar", ""),
                        c.get("content", ""),
                        int(c.get("like_count") or 0),
                        c.get("ip_location", ""),
                        c.get("upload_time", ""),
                        json.dumps(c.get("pictures", []), ensure_ascii=False),
                    ),
                )

        conn.commit()
        return session_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def query_history(keyword="", limit=50, offset=0):
    """查询搜索历史"""
    init_db()
    conn = get_conn()
    try:
        if keyword:
            rows = conn.execute(
                "SELECT * FROM search_sessions WHERE keyword LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (f"%{keyword}%", limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM search_sessions ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def query_notes_by_session(session_id):
    """查询某次搜索的所有笔记"""
    init_db()
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM notes WHERE session_id=?", (session_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def query_search_stats():
    """统计信息"""
    init_db()
    conn = get_conn()
    try:
        total_sessions = conn.execute("SELECT COUNT(*) FROM search_sessions").fetchone()[0]
        total_notes = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        total_comments = conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
        return {"sessions": total_sessions, "notes": total_notes, "comments": total_comments}
    finally:
        conn.close()
