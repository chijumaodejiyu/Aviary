# app.py - 所有功能在一个文件中
from flask import Flask, request, render_template, redirect
from markupsafe import escape, Markup
import bleach
import sqlite3
from datetime import datetime
import xml.etree.ElementTree as ET
import os
from contextlib import contextmanager

app = Flask(__name__)

class Database:
    def __init__(self):
        self.db_file = 'posts.db'
        
    @contextmanager
    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_file)
            try:
                yield conn
            finally:
                conn.close()
        except sqlite3.Error as e:
            print(f"数据库错误: {e}")
            raise
    
    def init_db(self):
        """初始化数据库"""
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
    
    def get_posts(self, limit=None):
        """获取文章列表"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            query = 'SELECT * FROM posts ORDER BY id DESC'
            if limit:
                # 使用参数化查询防止SQL注入
                return conn.execute(query + ' LIMIT ?', (limit,)).fetchall()
            return conn.execute(query).fetchall()
    
    def add_post(self, title, content):
        """添加新文章"""
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

    def get_post_by_id(self, post_id):
        """根据ID获取文章"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                'SELECT * FROM posts WHERE id = ?', 
                (post_id,)
            )
            return cursor.fetchone()

    def add_image(self, post_id, filename):
        """添加图片记录"""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO images (post_id, filename) VALUES (?, ?)',
                (post_id, filename)
            )
            conn.commit()

    def get_images_by_post(self, post_id):
        """获取文章关联的图片"""
        with self.get_connection() as conn:
            return conn.execute(
                'SELECT filename FROM images WHERE post_id = ?',
                (post_id,)
            ).fetchall()

    def update_post(self, post_id, title, content):
        """更新文章"""
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

    def delete_post(self, post_id):
        """删除文章"""
        with self.get_connection() as conn:
            conn.execute(
                'DELETE FROM posts WHERE id = ?',
                (post_id,)
            )
            conn.commit()

db = Database()

@app.errorhandler(500)
def internal_error(error):
    return "服务器内部错误", 500

@app.route('/error')
def error_page():
    return "发生错误，请稍后再试", 500





@app.route('/edit/<post_id>')
def edit_post(post_id):
    """编辑或新建文章(使用富文本编辑器)"""
    try:
        if post_id == 'new':
            return render_template('editor.html',
                                post_id=None,
                                title='',
                                content='')
        
        post_id = int(post_id)
        post = db.get_post_by_id(post_id)
        if post:
            return render_template('editor.html',
                                post_id=post_id,
                                title=post['title'],
                                content=post['content'])
        return redirect('/')
    except Exception as e:
        print(f"编辑错误: {e}")
        return redirect('/error')

@app.route('/save', methods=['POST'])
def save_post():
    """保存文章(新建或更新)"""
    try:
        post_id = request.form.get('post_id')
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            return "标题和内容不能为空", 400
        if len(title) > 100:
            return "标题过长", 400
        if len(content) > 50000:  # 提高限制以适应Base64图片
            return "内容过长", 400
            
        if post_id and post_id != 'None':
            db.update_post(post_id, title, content)
        else:
            db.add_post(title, content)
            
        return redirect('/')
    except Exception as e:
        print(f"保存错误: {e}")
        return redirect('/error')

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    """删除文章"""
    try:
        db.delete_post(post_id)
        return redirect('/')
    except Exception as e:
        print(f"删除错误: {e}")
        return redirect('/error')

@app.route('/')
def index():
    """集成页面主入口"""
    try:
        posts = db.get_posts()
        return render_template('integrated.html', 
                            posts=posts,
                            edit_mode=False,
                            post_id=None,
                            title='',
                            content='')
    except Exception as e:
        print(f"首页错误: {e}")
        return redirect('/error')

@app.route('/rss')
def rss_feed():
    """生成RSS订阅"""
    posts = db.get_posts(20)
    
    # 生成符合RSS 2.0规范的XML
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = "我的推文"
    ET.SubElement(channel, 'link').text = request.url_root
    ET.SubElement(channel, 'description').text = "我的最新推文更新"
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().isoformat()
    
    for post in posts:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = post['title']
        ET.SubElement(item, 'description').text = post['content']
        ET.SubElement(item, 'pubDate').text = post['created_at']
        ET.SubElement(item, 'guid').text = f"{request.url_root}post/{post['id']}"
        ET.SubElement(item, 'link').text = f"{request.url_root}post/{post['id']}"
    
    # 添加XML声明和正确的内容类型
    response = app.response_class(
        ET.tostring(rss, encoding='unicode'),
        mimetype='application/rss+xml'
    )
    return response

if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)