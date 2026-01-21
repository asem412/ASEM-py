"""
データベース設定
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLiteデータベースファイルのパス
SQLALCHEMY_DATABASE_URL = "sqlite:///./paid_leave.db"

# エンジン作成（check_same_thread=FalseはSQLite用）
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# セッションローカル
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス
Base = declarative_base()


def get_db():
    """
    DBセッションを取得する依存性注入用関数
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
