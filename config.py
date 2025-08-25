"""
Configuration settings for the Multi-Channel AI Customer Service System
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # Legacy SQLAlchemy config (kept for backward compatibility)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///hotel_service.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/hotel_service'
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL') or os.getenv('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Google Gemini API
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Hotel Information
    HOTEL_NAME = os.environ.get('HOTEL_NAME') or 'Grand Hotel'
    HOTEL_PHONE = os.environ.get('HOTEL_PHONE') or '+1234567890'
    HOTEL_EMAIL = os.environ.get('HOTEL_EMAIL') or 'info@grandhotel.com'
    HOTEL_ADDRESS = os.environ.get('HOTEL_ADDRESS') or '123 Main St, City, State 12345'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Use MongoDB Atlas in production
    MONGO_URI = os.environ.get('MONGODB_URI') or \
        'mongodb+srv://username:password@cluster0.mongodb.net/hotel_service?retryWrites=true&w=majority'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    MONGO_URI = 'mongodb://localhost:27017/hotel_service_test'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
