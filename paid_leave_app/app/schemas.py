"""
Pydanticスキーマ定義
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict


# 従業員スキーマ
class EmployeeBase(BaseModel):
    employee_code: str
    name: str
    hire_date: date
    active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    employee_code: Optional[str] = None
    name: Optional[str] = None
    hire_date: Optional[date] = None
    active: Optional[bool] = None


class Employee(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 付与スキーマ
class LeaveGrantBase(BaseModel):
    employee_id: int
    grant_date: date
    days: Decimal
    expire_date: date
    note: Optional[str] = None


class LeaveGrantCreate(LeaveGrantBase):
    pass


class LeaveGrant(LeaveGrantBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 取得スキーマ
class LeaveTakingBase(BaseModel):
    employee_id: int
    date: date
    kind: str  # 全日/午前休/午後休
    days: Decimal
    note: Optional[str] = None


class LeaveTakingCreate(BaseModel):
    employee_id: int
    date: date
    kind: str
    note: Optional[str] = None


class LeaveTakingUpdate(BaseModel):
    date: Optional[date] = None
    kind: Optional[str] = None
    note: Optional[str] = None


class LeaveTaking(LeaveTakingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 消化明細スキーマ
class LeaveUsage(BaseModel):
    id: int
    taking_id: int
    grant_id: int
    used_days: Decimal

    model_config = ConfigDict(from_attributes=True)
