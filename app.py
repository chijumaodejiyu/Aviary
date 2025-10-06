# Aviary - by RyanZ
from flask import Flask, request, render_template, redirect
from markupsafe import escape, Markup
import bleach
import sqlite3
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import logging
from contextlib import contextmanager
from database import Database
from config import Config

# 配置日志
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)

# 初始化数据库
db = Database()
Config.validate()  # 验证配置

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path}")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {error}")
    return render_template('500.html'), 500

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
        logger.error(f"Edit error: {e}")
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
        if len(content) > 50000:
            return "内容过长", 400
            
        if post_id and post_id != 'None':
            db.update_post(post_id, title, content)
        else:
            db.add_post(title, content)
            
        return redirect('/')
    except Exception as e:
        logger.error(f"Save error: {e}")
        return redirect('/error')

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    """删除文章"""
    try:
        db.delete_post(post_id)
        return redirect('/')
    except Exception as e:
        logger.error(f"Delete error: {e}")
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
        logger.error(f"Index error: {e}")
        return redirect('/error')

@app.route('/rss')
def rss_feed():
    """生成RSS订阅"""
    try:
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
        
        response = app.response_class(
            ET.tostring(rss, encoding='unicode'),
            mimetype='application/rss+xml'
        )
        return response
    except Exception as e:
        logger.error(f"RSS error: {e}")
        return redirect('/error')

if __name__ == '__main__':
    app.run(host=app.config.get('HOST', '0.0.0.0'), 
            port=app.config.get('PORT', 5000), 
            debug=app.config.get('DEBUG', True))
