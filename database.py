import sqlite3
import logging
from datetime import datetime
from contextlib import contextmanager
from markupsafe import escape
import bleach

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = 'posts.db'
        
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def init_db(self):
        """初始化数据库"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY,
                        title TEXT,
                        content TEXT,
                        created_at TEXT
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS images (
                        id INTEGER PRIMARY KEY,
                        post_id INTEGER,
                        filename TEXT,
                        FOREIGN KEY(post_id) REFERENCES posts(id)
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Init DB error: {e}")
            raise
    
    def get_posts(self, limit=None):
        """获取文章列表"""
        try:
            with self.get_connection() as conn:
                query = 'SELECT * FROM posts ORDER BY id DESC'
                if limit:
                    return conn.execute(query + ' LIMIT ?', (limit,)).fetchall()
                return conn.execute(query).fetchall()
        except Exception as e:
            logger.error(f"Get posts error: {e}")
            raise
    
    def add_post(self, title, content):
        """添加新文章"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)',
                    (escape(title), bleach.clean(content, 
                        tags=['b', 'i', 'u', 'h1', 'h2', 'h3', 'p', 'br', 'ul', 'ol', 'li', 'blockquote', 'img'],
                        attributes={
                            '*': ['style'],
                            'img': ['src', 'alt', 'style']
                        },
                        protocols=['http', 'https']
                    ), datetime.now().isoformat())
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Add post error: {e}")
            raise

    def get_post_by_id(self, post_id):
        """根据ID获取文章"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM posts WHERE id = ?', 
                    (post_id,)
                )
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get post by ID error: {e}")
            raise

    def add_image(self, post_id, filename):
        """添加图片记录"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'INSERT INTO images (post_id, filename) VALUES (?, ?)',
                    (post_id, filename)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Add image error: {e}")
            raise

    def get_images_by_post(self, post_id):
        """获取文章关联的图片"""
        try:
            with self.get_connection() as conn:
                return conn.execute(
                    'SELECT filename FROM images WHERE post_id = ?',
                    (post_id,)
                ).fetchall()
        except Exception as e:
            logger.error(f"Get images by post error: {e}")
            raise

    def update_post(self, post_id, title, content):
        """更新文章"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE posts SET title = ?, content = ? WHERE id = ?',
                    (escape(title), bleach.clean(content, 
                        tags=['b', 'i', 'u', 'h1', 'h2', 'h3', 'p', 'br', 'ul', 'ol', 'li', 'blockquote', 'img'],
                        attributes={
                            '*': ['style'],
                            'img': ['src', 'alt', 'style']
                        },
                        protocols=['http', 'https']
                    ), post_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Update post error: {e}")
            raise

    def delete_post(self, post_id):
        """删除文章"""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'DELETE FROM posts WHERE id = ?',
                    (post_id,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Delete post error: {e}")
            raise
