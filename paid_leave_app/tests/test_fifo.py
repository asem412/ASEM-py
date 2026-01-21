"""
FIFO消化と失効のテスト
"""
from datetime import date
from decimal import Decimal
from app import services, models


def test_fifo_allocation(db_session, sample_employee):
    """FIFO消化のテスト"""
    # 付与を2つ作成
    grant1 = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2022, 1, 1),
        days=Decimal("10"),
        expire_date=date(2024, 1, 1),
        note="付与1"
    )
    grant2 = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2023, 1, 1),
        days=Decimal("11"),
        expire_date=date(2025, 1, 1),
        note="付与2"
    )
    db_session.add_all([grant1, grant2])
    db_session.commit()

    # 取得を作成（全日：1.0日）
    taking = models.LeaveTaking(
        employee_id=sample_employee.id,
        date=date(2023, 5, 1),
        kind="全日",
        days=Decimal("1.0"),
        note="テスト取得"
    )
    db_session.add(taking)
    db_session.flush()

    # FIFO割り当て
    success = services.allocate_taking_to_grants(db_session, taking)
    assert success

    # grant1から先に消化されているか確認
    usages = db_session.query(models.LeaveUsage).filter(
        models.LeaveUsage.taking_id == taking.id
    ).all()

    assert len(usages) == 1
    assert usages[0].grant_id == grant1.id
    assert usages[0].used_days == Decimal("1.0")


def test_fifo_multiple_grants(db_session, sample_employee):
    """複数付与にまたがる消化のテスト"""
    # 付与を2つ作成
    grant1 = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2022, 1, 1),
        days=Decimal("0.5"),  # 0.5日だけ
        expire_date=date(2024, 1, 1),
        note="付与1"
    )
    grant2 = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2023, 1, 1),
        days=Decimal("11"),
        expire_date=date(2025, 1, 1),
        note="付与2"
    )
    db_session.add_all([grant1, grant2])
    db_session.commit()

    # 全日（1.0日）を取得
    taking = models.LeaveTaking(
        employee_id=sample_employee.id,
        date=date(2023, 5, 1),
        kind="全日",
        days=Decimal("1.0"),
        note="テスト取得"
    )
    db_session.add(taking)
    db_session.flush()

    # FIFO割り当て
    success = services.allocate_taking_to_grants(db_session, taking)
    assert success

    # grant1から0.5日、grant2から0.5日消化されているか確認
    usages = db_session.query(models.LeaveUsage).filter(
        models.LeaveUsage.taking_id == taking.id
    ).order_by(models.LeaveUsage.grant_id).all()

    assert len(usages) == 2
    assert usages[0].grant_id == grant1.id
    assert usages[0].used_days == Decimal("0.5")
    assert usages[1].grant_id == grant2.id
    assert usages[1].used_days == Decimal("0.5")


def test_insufficient_balance(db_session, sample_employee):
    """残日数不足のテスト"""
    # 付与を1つだけ作成（0.5日）
    grant = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2022, 1, 1),
        days=Decimal("0.5"),
        expire_date=date(2024, 1, 1),
        note="付与1"
    )
    db_session.add(grant)
    db_session.commit()

    # 全日（1.0日）を取得しようとする
    taking = models.LeaveTaking(
        employee_id=sample_employee.id,
        date=date(2023, 5, 1),
        kind="全日",
        days=Decimal("1.0"),
        note="テスト取得"
    )
    db_session.add(taking)
    db_session.flush()

    # FIFO割り当て（失敗するはず）
    success = services.allocate_taking_to_grants(db_session, taking)
    assert not success


def test_expiry_calculation(db_session, sample_employee):
    """失効計算のテスト"""
    # 既に失効した付与
    expired_grant = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2020, 1, 1),
        days=Decimal("10"),
        expire_date=date(2022, 1, 1),  # 既に失効
        note="失効済み付与"
    )
    # まだ有効な付与
    valid_grant = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2023, 1, 1),
        days=Decimal("11"),
        expire_date=date(2025, 1, 1),
        note="有効な付与"
    )
    db_session.add_all([expired_grant, valid_grant])
    db_session.commit()

    # 利用可能な付与を取得
    available = services.get_available_grants(db_session, sample_employee.id, date(2023, 6, 1))

    # 失効した付与は含まれない
    assert len(available) == 1
    assert available[0][0].id == valid_grant.id
    assert available[0][1] == Decimal("11")  # 残日数


def test_half_day_taking(db_session, sample_employee):
    """半日取得のテスト"""
    # 付与を作成
    grant = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2023, 1, 1),
        days=Decimal("10"),
        expire_date=date(2025, 1, 1),
        note="付与"
    )
    db_session.add(grant)
    db_session.commit()

    # 午前休（0.5日）を取得
    taking = models.LeaveTaking(
        employee_id=sample_employee.id,
        date=date(2023, 5, 1),
        kind="午前休",
        days=Decimal("0.5"),
        note="午前休"
    )
    db_session.add(taking)
    db_session.flush()

    # FIFO割り当て
    success = services.allocate_taking_to_grants(db_session, taking)
    assert success

    # 残日数確認
    summary = services.get_employee_summary(db_session, sample_employee.id, date(2023, 5, 2))
    assert summary["remaining"] == Decimal("9.5")


def test_recalculate_after_delete(db_session, sample_employee):
    """取得削除後の再計算テスト"""
    # 付与を作成
    grant = models.LeaveGrant(
        employee_id=sample_employee.id,
        grant_date=date(2023, 1, 1),
        days=Decimal("10"),
        expire_date=date(2025, 1, 1),
        note="付与"
    )
    db_session.add(grant)
    db_session.commit()

    # 取得を2つ作成
    taking1 = models.LeaveTaking(
        employee_id=sample_employee.id,
        date=date(2023, 5, 1),
        kind="全日",
        days=Decimal("1.0")
    )
    db_session.add(taking1)
    db_session.flush()
    services.allocate_taking_to_grants(db_session, taking1)

    taking2 = models.LeaveTaking(
        employee_id=sample_employee.id,
        date=date(2023, 5, 2),
        kind="全日",
        days=Decimal("1.0")
    )
    db_session.add(taking2)
    db_session.flush()
    services.allocate_taking_to_grants(db_session, taking2)

    # 残日数確認（10 - 2 = 8）
    summary = services.get_employee_summary(db_session, sample_employee.id, date(2023, 5, 3))
    assert summary["remaining"] == Decimal("8.0")

    # taking1を削除して再計算
    db_session.delete(taking1)
    db_session.flush()
    services.recalculate_usages_for_employee(db_session, sample_employee.id, date(2023, 5, 1))

    # 残日数確認（10 - 1 = 9）
    summary = services.get_employee_summary(db_session, sample_employee.id, date(2023, 5, 3))
    assert summary["remaining"] == Decimal("9.0")
