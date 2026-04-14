import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

# Base class para todos los modelos ORM
Base = declarative_base()

# Ruta a la base de datos SQLite (en el mismo directorio que app.py)
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///vendedor.db")

# Engine SQLAlchemy
engine = create_engine(DB_PATH, connect_args={"check_same_thread": False} if "sqlite" in DB_PATH else {})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency injection para obtener sesión de DB en Flask routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Crea todas las tablas en la base de datos"""
    from .models import Client, Lead, Message  # Import aquí para evitar circular imports
    Base.metadata.create_all(bind=engine)
