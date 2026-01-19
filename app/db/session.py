from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 建立資料庫引擎
# connect_args={"check_same_thread": False} 只適用於 SQLite
database_uri = settings.SQLALCHEMY_DATABASE_URI
connect_args = {"check_same_thread": False} if database_uri.startswith("sqlite") else {}

engine = create_engine(
    database_uri,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# 建立 SessionLocal 類別，每次實例化都會產生一個新的資料庫會話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別，所有的 Model 都繼承自這個類別
Base = declarative_base()

def get_db():
    """Dependency injection helper"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
