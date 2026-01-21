"""
データ状態を確認するスクリプト
"""
from app.database import SessionLocal
from app import models
from datetime import date

db = SessionLocal()

try:
    print("=== データ確認 ===\n")

    # 社員番号3の従業員を取得
    emp = db.query(models.Employee).filter(models.Employee.employee_code == "EMP003").first()

    if not emp:
        print("社員番号EMP003が見つかりません")
    else:
        print(f"従業員: {emp.name} (ID: {emp.id}, 社員番号: {emp.employee_code})")
        print(f"入社日: {emp.hire_date}\n")

        # 有効な付与を確認
        grants = db.query(models.LeaveGrant).filter(
            models.LeaveGrant.employee_id == emp.id,
            models.LeaveGrant.grant_date <= date.today(),
            models.LeaveGrant.expire_date > date.today()
        ).order_by(models.LeaveGrant.expire_date).all()

        print(f"有効な付与: {len(grants)}件")
        for g in grants:
            used_count = db.query(models.LeaveUsage).filter(
                models.LeaveUsage.grant_id == g.id
            ).count()
            used_days = sum(u.used_days for u in db.query(models.LeaveUsage).filter(
                models.LeaveUsage.grant_id == g.id
            ).all())
            print(f"  {g.grant_date}: {g.days}日 - 消化済{used_days}日 (Usageレコード: {used_count}件)")

        # 取得を確認
        takings = db.query(models.LeaveTaking).filter(
            models.LeaveTaking.employee_id == emp.id
        ).order_by(models.LeaveTaking.date).all()

        print(f"\n取得実績: {len(takings)}件")
        for t in takings:
            usage_count = db.query(models.LeaveUsage).filter(
                models.LeaveUsage.taking_id == t.id
            ).count()
            print(f"  {t.date}: {t.days}日 - LeaveUsage: {usage_count}件")
            if usage_count == 0:
                print(f"    ⚠️ この取得は付与に割り当てられていません！")

        print("\n=== 問題の診断 ===")
        takings_without_usage = [t for t in takings if db.query(models.LeaveUsage).filter(
            models.LeaveUsage.taking_id == t.id
        ).count() == 0]

        if takings_without_usage:
            print(f"⚠️ {len(takings_without_usage)}件の取得が付与に割り当てられていません")
            print("これが原因で残日数が減っていません")
        else:
            print("✓ 全ての取得が付与に割り当てられています")

finally:
    db.close()
