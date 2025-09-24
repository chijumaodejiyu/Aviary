# app.py - 所有功能在一个文件中
from flask import Flask, request, render_template, redirect
from markupsafe import escape
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
            conn.commit()
    
    def get_posts(self, limit=None):
        """获取文章列表"""
        with self.get_connection() as conn:
            query = 'SELECT * FROM posts ORDER BY id DESC'
            if limit:
                # 使用参数化查询防止SQL注入
                return conn.execute(query + ' LIMIT ?', (limit,)).fetchall()
            return conn.execute(query).fetchall()
    
    def add_post(self, title, content):
        """添加新文章"""
        with self.get_connection() as conn:
            conn.execute(
                'INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)',
                (escape(title), escape(content), datetime.now().isoformat())
            )
            conn.commit()

db = Database()

@app.errorhandler(500)
def internal_error(error):
    return "服务器内部错误", 500

@app.route('/')
def index():
    """首页显示最新推文"""
    try:
        posts = db.get_posts()
        return render_template('list.html', posts=posts)
    except Exception as e:
        print(f"首页错误: {e}")
        return redirect('/error')

@app.route('/error')
def error_page():
    return "发生错误，请稍后再试", 500

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    """发布新推文"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        
        if not title or not content:
            return "标题和内容不能为空", 400
        if len(title) > 100:
            return "标题过长", 400
        if len(content) > 5000:
            return "内容过长", 400
            
        db.add_post(title, content)
        return redirect('/')
    return render_template('editor.html')

@app.route('/rss')
def rss_feed():
    """生成RSS订阅"""
    posts = db.get_posts(20)
    
    # 简单生成RSS XML
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = "我的推文"
    
    for post in posts:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = post[1]
        ET.SubElement(item, 'description').text = post[2]
        ET.SubElement(item, 'pubDate').text = post[3]
    
    return ET.tostring(rss, encoding='unicode')

if __name__ == '__main__':
    db.init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)