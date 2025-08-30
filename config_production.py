import os
from datetime import timedelta

class ProductionConfig:
    """Produkční konfigurace aplikace Spolujízda"""
    
    # Základní nastavení
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-production-key-change-this'
    DEBUG = False
    TESTING = False
    
    # Databáze
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///production_spolujizda.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Session management
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS nastavení
    CORS_ORIGINS = [
        'https://yourdomain.com',
        'https://www.yourdomain.com'
    ]
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = CORS_ORIGINS
    
    # SMS API (Twilio example)
    SMS_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    SMS_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    SMS_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
    
    # Push notifikace (Firebase)
    FIREBASE_SERVER_KEY = os.environ.get('FIREBASE_SERVER_KEY')
    FIREBASE_SENDER_ID = os.environ.get('FIREBASE_SENDER_ID')
    
    # Mapové API
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
    HERE_API_KEY = os.environ.get('HERE_API_KEY')
    
    # Email nastavení
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/spolujizda.log'
    
    # Bezpečnostní hlavičky
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://unpkg.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: https:; connect-src 'self' wss: https:;"
    }
    
    # Validační pravidla
    VALIDATION_RULES = {
        'phone_regex': r'^\+420[0-9]{9}$',
        'password_min_length': 8,
        'max_message_length': 500,
        'max_rides_per_day': 10,
        'max_reservations_per_user': 5
    }
    
    # Geografické omezení (Česká republika)
    GEO_BOUNDS = {
        'min_lat': 48.5,
        'max_lat': 51.1,
        'min_lng': 12.0,
        'max_lng': 18.9
    }
    
    # Cache nastavení
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')
    
    @staticmethod
    def init_app(app):
        """Inicializace aplikace s produkční konfigurací"""
        
        # Logging setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            # Vytvoří logs složku
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            # Rotující log soubory
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_FILE,
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Spolujízda aplikace spuštěna v produkčním režimu')

class DevelopmentConfig:
    """Vývojová konfigurace"""
    
    SECRET_KEY = 'dev-secret-key'
    DEBUG = True
    TESTING = False
    DATABASE_URL = 'sqlite:///development_spolujizda.db'
    
    # Méně přísné bezpečnostní nastavení pro vývoj
    SESSION_COOKIE_SECURE = False
    CORS_ORIGINS = ['*']
    
    LOG_LEVEL = 'DEBUG'
    
    @staticmethod
    def init_app(app):
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Spolujízda aplikace spuštěna ve vývojovém režimu')

class TestingConfig:
    """Testovací konfigurace"""
    
    SECRET_KEY = 'test-secret-key'
    DEBUG = False
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    @staticmethod
    def init_app(app):
        pass

# Konfigurace podle prostředí
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}