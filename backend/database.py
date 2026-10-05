"""
Database models and connection using SQLAlchemy for SQLite.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "ai_spends.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SpendEvent(Base):
    __tablename__ = "spend_events"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True, nullable=False)
    environment = Column(String, default="production")  # production, staging, development
    provider = Column(String, index=True, nullable=False)  # openai, anthropic, google, deepseek, mistral
    model_id = Column(String, index=True, nullable=False)  # gpt-4o, claude-3-5-sonnet, etc.
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    cached_tokens = Column(Integer, default=0)
    reasoning_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    prompt_cost_usd = Column(Float, default=0.0)
    completion_cost_usd = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    
    latency_ms = Column(Integer, default=0)
    http_status_code = Column(Integer, default=200)
    feature_tag = Column(String, default="general")
    user_identifier = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ModelRateCard(Base):
    __tablename__ = "model_rate_cards"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    tier = Column(String, default="frontier")  # frontier, economy, reasoning
    
    prompt_price_per_million = Column(Float, nullable=False)
    completion_price_per_million = Column(Float, nullable=False)
    cached_prompt_price_per_million = Column(Float, default=0.0)
    reasoning_price_per_million = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, unique=True, index=True, nullable=False)
    monthly_limit_usd = Column(Float, nullable=False)
    alert_threshold_percent = Column(Float, default=80.0)
    hard_cap_enabled = Column(Boolean, default=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
