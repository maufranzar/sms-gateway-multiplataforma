"""
Configuración de la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base
from config import settings
import logging

logger = logging.getLogger(__name__)

# Crear engine de la base de datos
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Crear sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Crea todas las tablas en la base de datos"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
        raise

def get_db() -> Session:
    """Obtiene una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_sync() -> Session:
    """Obtiene una sesión de base de datos síncrona"""
    return SessionLocal()
