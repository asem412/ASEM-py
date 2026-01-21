"""
データ整合性修正スクリプト
全従業員の取得実績を再計算して整合性を保つ
"""
from app.database import SessionLocal
from app import models, services

def fix_data_integrity():
    """全従業員のデータ整合性を修正"""
    db = SessionLocal()

    try:
        print("データ整合性修正を開始します...")
        print()

        # 全従業員を取得
        employees = db.query(models.Employee).all()

        for emp in employees:
            print(f"処理中: {emp.name} (ID: {emp.id})")

            # この従業員の全ての消化明細を削除
            deleted_count = db.query(models.LeaveUsage).filter(
                models.LeaveUsage.taking_id.in_(
                    db.query(models.LeaveTaking.id).filter(
                        models.LeaveTaking.employee_id == emp.id
                    )
                )
            ).delete(synchronize_session=False)

            print(f"  古い消化明細を{deleted_count}件削除")

            # 全ての取得実績を日付順に再割り当て
            takings = db.query(models.LeaveTaking).filter(
                models.LeaveTaking.employee_id == emp.id
            ).order_by(models.LeaveTaking.date).all()

            success_count = 0
            fail_count = 0

            for taking in takings:
                success = services.allocate_taking_to_grants(db, taking)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    print(f"  ⚠️ 警告: {taking.date}の取得({taking.days}日)を割り当てできませんでした（残日数不足）")

            print(f"  取得実績を再割り当て: 成功{success_count}件, 失敗{fail_count}件")

            # サマリーを表示
            summary = services.get_employee_summary(db, emp.id)
            print(f"  → 現在の残日数: {summary['remaining']}日")
            print()

        print("✅ データ整合性修正が完了しました！")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    fix_data_integrity()
