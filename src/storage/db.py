from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import yaml
import os

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    asin = Column(String(20), unique=True, index=True)
    title = Column(String(500))
    category = Column(String(100))
    price = Column(Float)
    bsr_current = Column(Integer)
    bsr_previous = Column(Integer)
    bsr_velocity = Column(Float)  # Rate of BSR change
    momentum_score = Column(Float)
    confidence_level = Column(String(20))  # low/med/high
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_trending = Column(Boolean, default=False)

class TrendData(Base):
    __tablename__ = "trend_data"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200))
    platform = Column(String(50))  # google_trends, reddit, tiktok
    volume_score = Column(Float)
    velocity_score = Column(Float)  # Rate of change
    sentiment_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_asin = Column(String(20))
    alert_type = Column(String(50))  # momentum_spike, new_trend, etc
    message = Column(Text)
    momentum_score = Column(Float)
    confidence = Column(String(20))
    sent_at = Column(DateTime, default=datetime.utcnow)
    telegram_sent = Column(Boolean, default=False)

class ShopifyStore(Base):
    __tablename__ = "shopify_stores"
    
    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String(200))
    url = Column(String(500))
    product_count = Column(Integer)
    momentum_score = Column(Float)
    last_checked = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self, config_path="config.yaml"):
        self.engine = None
        self.SessionLocal = None
        self.load_config(config_path)
        self.init_db()
    
    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.db_url = config['database']['url']
        else:
            # Fallback to default
            self.db_url = "sqlite:///listing_radar.db"
    
    def init_db(self):
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def close(self):
        if self.engine:
            self.engine.dispose()

# Global instance
db_manager = DatabaseManager()

def get_db():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()