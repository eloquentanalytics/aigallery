from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import os
from ..utils.config import get_settings

# Get database URL from settings (supports both SQLite and Postgres)
settings = get_settings()
DATABASE_URL = settings.database_url

# Configure engine based on database type
if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    # Postgres configuration for Vercel/production
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
else:
    # SQLite configuration for local development
    os.makedirs("data", exist_ok=True)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    stripe_customer_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship to renders
    renders = relationship("Render", back_populates="user")

class Render(Base):
    __tablename__ = "renders"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for public gallery
    style_phrase = Column(String, nullable=False, index=True)
    model_key = Column(String, nullable=False, index=True)  # "replicate:sdxl", "openai:dalle3"
    base_prompt = Column(Text, nullable=False)
    image_path = Column(String, nullable=False)
    thumb_path = Column(String, nullable=False)
    input_image_path = Column(String, nullable=True)  # For img2img
    status = Column(String, nullable=False, default="pending", index=True)  # pending, done, failed
    cost_credits = Column(Integer, default=1)
    render_metadata = Column(JSON, nullable=True)  # Generation params, provider response
    stripe_event_id = Column(String, nullable=True)  # For idempotency
    created_at = Column(DateTime, server_default=func.now())

    # Relationship to user
    user = relationship("User", back_populates="renders")

def create_tables():
    """Create database tables if they don't exist"""
    # Only create data directory for SQLite
    if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")):
        os.makedirs("data", exist_ok=True)

    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()