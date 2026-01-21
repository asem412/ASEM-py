"""
ビジネスロジック層
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Tuple, Dict
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app import models


# 付与日数テーブル（入社からの経過年数に応じた付与日数）
GRANT_DAYS_TABLE = {
    0: Decimal("10"),   # 入社6か月後（初回）
    1: Decimal("11"),   # 1年6か月後
    2: Decimal("12"),   # 2年6か月後
    3: Decimal("14"),   # 3年6か月後
    4: Decimal("16"),   # 4年6か月後
    5: Decimal("18"),   # 5年6か月後
    6: Decimal("20"),   # 6年6か月後以降
}


def calculate_grant_date_and_days(hire_date: date, index: int) -> Tuple[date, Decimal]:
    """
    付与日と付与日数を計算

    Args:
        hire_date: 入社日
        index: 何回目の付与か（0が初回）

    Returns:
        (付与日, 付与日数)
    """
    if index == 0:
        # 初回は入社6か月後
        grant_date = hire_date + relativedelta(months=6)
    else:
        # 2回目以降は初回から1年ごと
        grant_date = hire_date + relativedelta(months=6 + (index * 12))

    # 付与日数を取得（6回目以降は全て20日）
    days_index = min(index, 6)
    days = GRANT_DAYS_TABLE[days_index]

    return grant_date, days


def generate_grants_for_employee(db: Session, employee: models.Employee, as_of_date: date = None) -> int:
    """
    従業員の付与を自動生成する

    Args:
        db: DBセッション
        employee: 従業員
        as_of_date: この日付までの付与を生成（Noneの場合は今日）

    Returns:
        生成した付与の数
    """
    if as_of_date is None:
        as_of_date = date.today()

    # 既存の付与を取得
    existing_grants = db.query(models.LeaveGrant).filter(
        models.LeaveGrant.employee_id == employee.id
    ).order_by(models.LeaveGrant.grant_date).all()

    existing_grant_dates = {g.grant_date for g in existing_grants}

    generated_count = 0
    index = 0

    while True:
        grant_date, days = calculate_grant_date_and_days(employee.hire_date, index)

        # as_of_dateを超えたら終了
        if grant_date > as_of_date:
            break

        # 既に存在する場合はスキップ
        if grant_date not in existing_grant_dates:
            # 失効日は付与日+2年
            expire_date = grant_date + relativedelta(years=2)

            grant = models.LeaveGrant(
                employee_id=employee.id,
                grant_date=grant_date,
                days=days,
                expire_date=expire_date,
                note=f"自動付与{index + 1}回目"
            )
            db.add(grant)
            generated_count += 1

        index += 1

    if generated_count > 0:
        db.commit()

    return generated_count


def generate_grants_for_all(db: Session, as_of_date: date = None) -> Dict[str, int]:
    """
    全従業員の付与を自動生成

    Args:
        db: DBセッション
        as_of_date: この日付までの付与を生成

    Returns:
        {"total": 総生成数, "employee_id": 生成数, ...}
    """
    if as_of_date is None:
        as_of_date = date.today()

    employees = db.query(models.Employee).filter(
        models.Employee.active == True
    ).all()

    result = {"total": 0}

    for emp in employees:
        count = generate_grants_for_employee(db, emp, as_of_date)
        result[f"employee_{emp.id}"] = count
        result["total"] += count

    return result


def get_available_grants(db: Session, employee_id: int, as_of_date: date = None) -> List[Tuple[models.LeaveGrant, Decimal]]:
    """
    従業員の利用可能な付与一覧を取得（FIFO順、失効日が近い順）

    Args:
        db: DBセッション
        employee_id: 従業員ID
        as_of_date: 基準日（この日までに失効していない付与）

    Returns:
        [(付与, 残日数), ...]
    """
    if as_of_date is None:
        as_of_date = date.today()

    # 有効な付与を取得（失効日が基準日以降、付与日が基準日以前）
    grants = db.query(models.LeaveGrant).filter(
        and_(
            models.LeaveGrant.employee_id == employee_id,
            models.LeaveGrant.grant_date <= as_of_date,
            models.LeaveGrant.expire_date > as_of_date
        )
    ).order_by(models.LeaveGrant.expire_date, models.LeaveGrant.grant_date).all()

    result = []
    for grant in grants:
        # この付与から既に消化された日数を計算
        used = db.query(func.sum(models.LeaveUsage.used_days)).filter(
            models.LeaveUsage.grant_id == grant.id
        ).scalar() or Decimal("0")

        remaining = grant.days - used
        if remaining > 0:
            result.append((grant, remaining))

    return result


def allocate_taking_to_grants(db: Session, taking: models.LeaveTaking) -> bool:
    """
    取得実績を付与に割り当てる（FIFO）

    Args:
        db: DBセッション
        taking: 取得実績

    Returns:
        成功したかどうか
    """
    # 既存の割り当てを削除
    db.query(models.LeaveUsage).filter(
        models.LeaveUsage.taking_id == taking.id
    ).delete()

    # 利用可能な付与を取得
    available = get_available_grants(db, taking.employee_id, taking.date)

    remaining_to_allocate = taking.days

    for grant, grant_remaining in available:
        if remaining_to_allocate <= 0:
            break

        # この付与から割り当てる日数
        to_use = min(remaining_to_allocate, grant_remaining)

        usage = models.LeaveUsage(
            taking_id=taking.id,
            grant_id=grant.id,
            used_days=to_use
        )
        db.add(usage)

        remaining_to_allocate -= to_use

    # 割り当て不足がある場合はエラー
    if remaining_to_allocate > 0:
        db.rollback()
        return False

    db.commit()
    return True


def recalculate_usages_for_employee(db: Session, employee_id: int, from_date: date = None):
    """
    従業員の取得実績を再計算（修正/削除時に使用）

    Args:
        db: DBセッション
        employee_id: 従業員ID
        from_date: この日付以降の取得を再計算（Noneの場合は全て）
    """
    # 対象の取得実績を取得
    query = db.query(models.LeaveTaking).filter(
        models.LeaveTaking.employee_id == employee_id
    )

    if from_date:
        query = query.filter(models.LeaveTaking.date >= from_date)

    takings = query.order_by(models.LeaveTaking.date).all()

    # 既存の割り当てを削除
    for taking in takings:
        db.query(models.LeaveUsage).filter(
            models.LeaveUsage.taking_id == taking.id
        ).delete()

    # 再割り当て
    for taking in takings:
        allocate_taking_to_grants(db, taking)


def get_employee_summary(db: Session, employee_id: int, as_of_date: date = None) -> Dict:
    """
    従業員の有給サマリーを取得

    Returns:
        {
            "total_granted": 付与合計,
            "total_taken": 取得合計,
            "total_expired": 失効合計,
            "remaining": 残日数,
            "grants": [(付与情報, 残日数), ...],
            "next_expiry_date": 次の失効日,
            "next_expiry_days": 次に失効する日数
        }
    """
    if as_of_date is None:
        as_of_date = date.today()

    # 全付与を取得
    all_grants = db.query(models.LeaveGrant).filter(
        models.LeaveGrant.employee_id == employee_id,
        models.LeaveGrant.grant_date <= as_of_date
    ).all()

    total_granted = sum(g.days for g in all_grants)

    # 失効した付与
    expired_grants = [g for g in all_grants if g.expire_date <= as_of_date]
    total_expired = sum(g.days for g in expired_grants)

    # 取得合計
    total_taken = db.query(func.sum(models.LeaveTaking.days)).filter(
        models.LeaveTaking.employee_id == employee_id,
        models.LeaveTaking.date <= as_of_date
    ).scalar() or Decimal("0")

    # 有効な付与の残日数
    available = get_available_grants(db, employee_id, as_of_date)
    remaining = sum(r for _, r in available)

    # 次の失効情報
    next_expiry_date = None
    next_expiry_days = Decimal("0")
    if available:
        next_grant, next_remaining = available[0]
        next_expiry_date = next_grant.expire_date
        next_expiry_days = next_remaining

    return {
        "total_granted": total_granted,
        "total_taken": total_taken,
        "total_expired": total_expired,
        "remaining": remaining,
        "grants": available,
        "next_expiry_date": next_expiry_date,
        "next_expiry_days": next_expiry_days
    }


def get_taking_kind_days(kind: str) -> Decimal:
    """
    取得種別から日数を取得

    Args:
        kind: 全日/午前休/午後休

    Returns:
        日数
    """
    if kind == "全日":
        return Decimal("1.0")
    elif kind in ["午前休", "午後休"]:
        return Decimal("0.5")
    else:
        raise ValueError(f"不正な取得種別: {kind}")
