"""
Database models for Knowledge Enhancer Bot
Tracks users, ratings, daily questions, and transactions
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os

Base = declarative_base()


class User(Base):
    """User model - tracks profile, credits, and statistics"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, unique=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    
    # Daily free questions (resets daily at midnight)
    free_questions_today = Column(Integer, default=5)  # 5 free/day
    last_daily_reset = Column(DateTime, default=datetime.utcnow)
    
    # Premium subscription
    is_premium = Column(Boolean, default=False)
    premium_type = Column(String(20), nullable=True)  # "weekly", "monthly", "yearly"
    premium_expires_at = Column(DateTime, nullable=True)
    
    # Rating system
    current_rating = Column(Float, default=0.0)
    total_correct = Column(Integer, default=0)
    total_wrong = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    
    # Streaks and stats
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    
    # Daily tracking
    questions_today = Column(Integer, default=0)
    last_reset = Column(DateTime, default=datetime.utcnow)
    
    # Account
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(user_id={self.user_id}, rating={self.current_rating}, streak={self.current_streak})>"


class UserProgress(Base):
    """Track user progress per subject and difficulty"""
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    subject = Column(String(100), nullable=False)  # Math, Physics, Chemistry, etc.
    difficulty = Column(Integer, nullable=False)  # 0-10=Easy, 11-20=Medium, etc.
    correct_count = Column(Integer, default=0)
    wrong_count = Column(Integer, default=0)
    last_attempted = Column(DateTime, default=datetime.utcnow)


class Question(Base):
    """Store generated questions for reference"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    subject = Column(String(100), nullable=False)
    difficulty = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON string
    correct_index = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    """Track credit purchases"""
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    amount_paid = Column(Float, nullable=False)  # INR
    credits_added = Column(Integer, nullable=False)
    payment_method = Column(String(50), default="telegram_stars")
    payment_status = Column(String(20), default="pending")
    telegram_payment_id = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Database initialization
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./knowledgebot.db")


async def init_db():
    """Initialize database and create tables"""
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool if "sqlite" in DATABASE_URL else None,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine


def get_session_maker(engine):
    """Create async session factory"""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        future=True
    )
