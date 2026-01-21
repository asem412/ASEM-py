"""
サンプルデータを作成するスクリプト
"""
from datetime import date
from app.database import SessionLocal
from app import models, services

def create_sample_data():
    """サンプルデータを作成"""
    db = SessionLocal()

    try:
        # 既存のデータを確認
        existing_count = db.query(models.Employee).count()
        if existing_count > 0:
            print(f"既に{existing_count}名の従業員が登録されています。")
            return

        # サンプル従業員を作成
        employees_data = [
            {"code": "EMP001", "name": "田中 太郎", "hire_date": date(2018, 4, 1)},
            {"code": "EMP002", "name": "佐藤 花子", "hire_date": date(2019, 7, 15)},
            {"code": "EMP003", "name": "鈴木 一郎", "hire_date": date(2020, 10, 1)},
            {"code": "EMP004", "name": "高橋 美咲", "hire_date": date(2021, 4, 1)},
            {"code": "EMP005", "name": "伊藤 健太", "hire_date": date(2022, 1, 15)},
            {"code": "EMP006", "name": "渡辺 由美", "hire_date": date(2022, 8, 1)},
            {"code": "EMP007", "name": "山本 直樹", "hire_date": date(2023, 4, 1)},
            {"code": "EMP008", "name": "中村 愛子", "hire_date": date(2023, 10, 1)},
            {"code": "EMP009", "name": "小林 誠", "hire_date": date(2024, 1, 15)},
        ]

        employees = []
        for emp_data in employees_data:
            emp = models.Employee(
                employee_code=emp_data["code"],
                name=emp_data["name"],
                hire_date=emp_data["hire_date"],
                active=True
            )
            db.add(emp)
            employees.append(emp)

        db.commit()
        print(f"{len(employees)}名の従業員を作成しました。")

        # 各従業員の付与を自動生成
        for emp in employees:
            db.refresh(emp)
            count = services.generate_grants_for_employee(db, emp)
            print(f"{emp.name}さんに{count}件の付与を生成しました。")

        # サンプルの取得実績を作成
        print("\nサンプルの取得実績を作成中...")

        # 田中さん（EMP001）の取得実績
        emp1 = employees[0]
        db.refresh(emp1)
        takings = [
            models.LeaveTaking(
                employee_id=emp1.id,
                date=date(2024, 5, 10),
                kind="全日",
                days=1.0,
                note="私用"
            ),
            models.LeaveTaking(
                employee_id=emp1.id,
                date=date(2024, 7, 15),
                kind="午前休",
                days=0.5,
                note="通院"
            ),
        ]

        for taking in takings:
            db.add(taking)
            db.flush()
            services.allocate_taking_to_grants(db, taking)

        print(f"{emp1.name}さんに{len(takings)}件の取得実績を作成しました。")

        # 佐藤さん（EMP002）の取得実績
        emp2 = employees[1]
        db.refresh(emp2)
        takings2 = [
            models.LeaveTaking(
                employee_id=emp2.id,
                date=date(2024, 6, 3),
                kind="全日",
                days=1.0,
                note="家族旅行"
            ),
        ]

        for taking in takings2:
            db.add(taking)
            db.flush()
            services.allocate_taking_to_grants(db, taking)

        print(f"{emp2.name}さんに{len(takings2)}件の取得実績を作成しました。")

        print("\n✅ サンプルデータの作成が完了しました！")
        print("\nブラウザで http://127.0.0.1:8000/ にアクセスして確認してください。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
