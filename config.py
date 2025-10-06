import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 应用配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # 数据库配置
    DATABASE_FILE = os.getenv('DATABASE_FILE', 'posts.db')
    DATABASE_TIMEOUT = int(os.getenv('DATABASE_TIMEOUT', '30'))
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # 安全配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # RSS配置
    RSS_TITLE = os.getenv('RSS_TITLE', '我的推文')
    RSS_DESCRIPTION = os.getenv('RSS_DESCRIPTION', '我的最新推文更新')
    RSS_MAX_ITEMS = int(os.getenv('RSS_MAX_ITEMS', '20'))
    
    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key':
            if not cls.DEBUG:
                raise ValueError("在生产环境中必须设置SECRET_KEY")
        
        if not cls.DATABASE_FILE:
            raise ValueError("必须设置DATABASE_FILE")
            
        if cls.PORT < 1 or cls.PORT > 65535:
            raise ValueError("PORT必须在1-65535之间")
