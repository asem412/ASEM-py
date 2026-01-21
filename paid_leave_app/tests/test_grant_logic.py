"""
付与ロジックのテスト
"""
from datetime import date
from decimal import Decimal
from app import services


def test_calculate_grant_date_and_days():
    """付与日と付与日数の計算テスト"""
    hire_date = date(2020, 4, 1)

    # 初回（入社6か月後）
    grant_date, days = services.calculate_grant_date_and_days(hire_date, 0)
    assert grant_date == date(2020, 10, 1)
    assert days == Decimal("10")

    # 2回目（入社1年6か月後）
    grant_date, days = services.calculate_grant_date_and_days(hire_date, 1)
    assert grant_date == date(2021, 10, 1)
    assert days == Decimal("11")

    # 3回目（入社2年6か月後）
    grant_date, days = services.calculate_grant_date_and_days(hire_date, 2)
    assert grant_date == date(2022, 10, 1)
    assert days == Decimal("12")

    # 7回目以降は20日
    grant_date, days = services.calculate_grant_date_and_days(hire_date, 7)
    assert grant_date == date(2027, 10, 1)
    assert days == Decimal("20")


def test_generate_grants_for_employee(db_session, sample_employee):
    """従業員の付与生成テスト"""
    # 2023年1月1日までの付与を生成
    as_of_date = date(2023, 1, 1)
    count = services.generate_grants_for_employee(db_session, sample_employee, as_of_date)

    # 2020年4月1日入社 → 2020/10/1, 2021/10/1, 2022/10/1 の3回
    assert count == 3

    # 付与データを確認
    grants = db_session.query(services.models.LeaveGrant).filter(
        services.models.LeaveGrant.employee_id == sample_employee.id
    ).order_by(services.models.LeaveGrant.grant_date).all()

    assert len(grants) == 3
    assert grants[0].days == Decimal("10")
    assert grants[1].days == Decimal("11")
    assert grants[2].days == Decimal("12")

    # 失効日は付与日+2年
    assert grants[0].expire_date == date(2022, 10, 1)
    assert grants[1].expire_date == date(2023, 10, 1)

    # 二重生成されないことを確認
    count2 = services.generate_grants_for_employee(db_session, sample_employee, as_of_date)
    assert count2 == 0


def test_get_taking_kind_days():
    """取得種別から日数を取得するテスト"""
    assert services.get_taking_kind_days("全日") == Decimal("1.0")
    assert services.get_taking_kind_days("午前休") == Decimal("0.5")
    assert services.get_taking_kind_days("午後休") == Decimal("0.5")
