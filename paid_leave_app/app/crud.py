"""
CRUD操作
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app import models, schemas, services


# 従業員CRUD
def get_employee(db: Session, employee_id: int) -> Optional[models.Employee]:
    """従業員を取得"""
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()


def get_employee_by_code(db: Session, employee_code: str) -> Optional[models.Employee]:
    """従業員を社員番号で取得"""
    return db.query(models.Employee).filter(models.Employee.employee_code == employee_code).first()


def get_employees(db: Session, active_only: bool = False) -> List[models.Employee]:
    """従業員一覧を取得"""
    query = db.query(models.Employee)
    if active_only:
        query = query.filter(models.Employee.active == True)
    return query.order_by(models.Employee.employee_code).all()


def create_employee(db: Session, employee: schemas.EmployeeCreate) -> models.Employee:
    """従業員を作成"""
    db_employee = models.Employee(**employee.model_dump())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def update_employee(db: Session, employee_id: int, employee: schemas.EmployeeUpdate) -> Optional[models.Employee]:
    """従業員を更新"""
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None

    update_data = employee.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_employee, key, value)

    db.commit()
    db.refresh(db_employee)
    return db_employee


def delete_employee(db: Session, employee_id: int) -> bool:
    """従業員を削除（論理削除）"""
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return False

    db_employee.active = False
    db.commit()
    return True


# 付与CRUD
def get_grants(db: Session, employee_id: int) -> List[models.LeaveGrant]:
    """従業員の付与一覧を取得"""
    return db.query(models.LeaveGrant).filter(
        models.LeaveGrant.employee_id == employee_id
    ).order_by(models.LeaveGrant.grant_date).all()


def create_grant(db: Session, grant: schemas.LeaveGrantCreate) -> models.LeaveGrant:
    """付与を作成"""
    db_grant = models.LeaveGrant(**grant.model_dump())
    db.add(db_grant)
    db.commit()
    db.refresh(db_grant)
    return db_grant


# 取得CRUD
def get_taking(db: Session, taking_id: int) -> Optional[models.LeaveTaking]:
    """取得実績を取得"""
    return db.query(models.LeaveTaking).filter(models.LeaveTaking.id == taking_id).first()


def get_takings(db: Session, employee_id: int) -> List[models.LeaveTaking]:
    """従業員の取得実績一覧を取得"""
    return db.query(models.LeaveTaking).filter(
        models.LeaveTaking.employee_id == employee_id
    ).order_by(models.LeaveTaking.date.desc()).all()


def create_taking(db: Session, taking: schemas.LeaveTakingCreate) -> Optional[models.LeaveTaking]:
    """
    取得実績を作成

    Returns:
        作成した取得実績（残数不足の場合はNone）
    """
    # 日数を計算
    days = services.get_taking_kind_days(taking.kind)

    db_taking = models.LeaveTaking(
        employee_id=taking.employee_id,
        date=taking.date,
        kind=taking.kind,
        days=days,
        note=taking.note
    )
    db.add(db_taking)
    db.flush()  # IDを取得するためflush

    # 付与に割り当て
    success = services.allocate_taking_to_grants(db, db_taking)

    if not success:
        db.rollback()
        return None

    db.refresh(db_taking)
    return db_taking


def update_taking(db: Session, taking_id: int, taking: schemas.LeaveTakingUpdate) -> Optional[models.LeaveTaking]:
    """
    取得実績を更新

    Returns:
        更新した取得実績（残数不足の場合はNone）
    """
    db_taking = get_taking(db, taking_id)
    if not db_taking:
        return None

    # 更新データを適用
    update_data = taking.model_dump(exclude_unset=True)

    # 種別が変更された場合は日数も更新
    if "kind" in update_data:
        update_data["days"] = services.get_taking_kind_days(update_data["kind"])

    for key, value in update_data.items():
        setattr(db_taking, key, value)

    db.flush()

    # この取得以降を再計算
    services.recalculate_usages_for_employee(
        db, db_taking.employee_id, db_taking.date
    )

    db.commit()
    db.refresh(db_taking)
    return db_taking


def delete_taking(db: Session, taking_id: int) -> bool:
    """
    取得実績を削除
    """
    db_taking = get_taking(db, taking_id)
    if not db_taking:
        return False

    employee_id = db_taking.employee_id
    taking_date = db_taking.date

    # 削除
    db.delete(db_taking)
    db.flush()

    # この日以降を再計算
    services.recalculate_usages_for_employee(db, employee_id, taking_date)

    db.commit()
    return True
