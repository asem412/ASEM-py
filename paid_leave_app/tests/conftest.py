"""
テスト用の設定
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.database import Base
from app import models


# テスト用のインメモリデータベース
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """テスト用DBセッションを作成"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # テーブル作成
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_employee(db_session):
    """サンプル従業員を作成"""
    employee = models.Employee(
        employee_code="EMP001",
        name="テスト太郎",
        hire_date=date(2020, 4, 1),
        active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee
