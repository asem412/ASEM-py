"""
データモデル定義
"""
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Employee(Base):
    """従業員マスタ"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    hire_date = Column(Date, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # リレーション
    grants = relationship("LeaveGrant", back_populates="employee", cascade="all, delete-orphan")
    takings = relationship("LeaveTaking", back_populates="employee", cascade="all, delete-orphan")


class LeaveGrant(Base):
    """有給付与実績"""
    __tablename__ = "leave_grants"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    grant_date = Column(Date, nullable=False)
    days = Column(Numeric(precision=10, scale=1), nullable=False)  # 付与日数（10.0など）
    expire_date = Column(Date, nullable=False)  # 失効日（付与日+2年）
    note = Column(Text, nullable=True)  # 備考
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # リレーション
    employee = relationship("Employee", back_populates="grants")
    usages = relationship("LeaveUsage", back_populates="grant", cascade="all, delete-orphan")


class LeaveTaking(Base):
    """有給取得実績"""
    __tablename__ = "leave_takings"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)  # 取得日
    kind = Column(String(20), nullable=False)  # 種別: 全日/午前休/午後休
    days = Column(Numeric(precision=10, scale=1), nullable=False)  # 取得日数（1.0 or 0.5）
    note = Column(Text, nullable=True)  # メモ
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # リレーション
    employee = relationship("Employee", back_populates="takings")
    usages = relationship("LeaveUsage", back_populates="taking", cascade="all, delete-orphan")


class LeaveUsage(Base):
    """有給消化明細（どの付与から何日引いたか）"""
    __tablename__ = "leave_usages"

    id = Column(Integer, primary_key=True, index=True)
    taking_id = Column(Integer, ForeignKey("leave_takings.id"), nullable=False, index=True)
    grant_id = Column(Integer, ForeignKey("leave_grants.id"), nullable=False, index=True)
    used_days = Column(Numeric(precision=10, scale=1), nullable=False)  # 消化日数

    # リレーション
    taking = relationship("LeaveTaking", back_populates="usages")
    grant = relationship("LeaveGrant", back_populates="usages")
