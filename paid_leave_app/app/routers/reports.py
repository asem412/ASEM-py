"""
レポート・CSV出力ルーター
"""
import csv
import io
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from decimal import Decimal

from app import crud, services, models
from app.database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def reports_index(request: Request):
    """レポート選択画面"""
    return templates.TemplateResponse(
        "reports/index.html",
        {"request": request}
    )


@router.get("/csv", response_class=HTMLResponse)
async def csv_form(
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """CSV出力フォーム"""
    # デフォルト期間: 今年の1/1から今日まで
    today = date.today()
    default_from = date(today.year, 1, 1)
    default_to = today

    return templates.TemplateResponse(
        "reports/csv_form.html",
        {
            "request": request,
            "from_date": from_date or default_from.isoformat(),
            "to_date": to_date or default_to.isoformat()
        }
    )


@router.get("/csv/download")
async def download_csv(
    from_date: str = Query(...),
    to_date: str = Query(...),
    db: Session = Depends(get_db)
):
    """全員まとめCSVをダウンロード"""
    start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(to_date, "%Y-%m-%d").date()

    employees = crud.get_employees(db)

    # CSVデータを作成
    output = io.StringIO()
    writer = csv.writer(output)

    # ヘッダー
    writer.writerow([
        "従業員ID",
        "氏名",
        "入社日",
        "在籍状況",
        "期間内付与合計",
        "期間内取得合計",
        "期間内失効合計",
        "現在残日数",
        "直近付与日",
        "次に失効する日",
        "次に失効する残日数"
    ])

    # 各従業員のデータ
    for emp in employees:
        # 期間内の付与合計
        period_granted = db.query(func.sum(models.LeaveGrant.days)).filter(
            and_(
                models.LeaveGrant.employee_id == emp.id,
                models.LeaveGrant.grant_date >= start_date,
                models.LeaveGrant.grant_date <= end_date
            )
        ).scalar() or Decimal("0")

        # 期間内の取得合計
        period_taken = db.query(func.sum(models.LeaveTaking.days)).filter(
            and_(
                models.LeaveTaking.employee_id == emp.id,
                models.LeaveTaking.date >= start_date,
                models.LeaveTaking.date <= end_date
            )
        ).scalar() or Decimal("0")

        # 期間内の失効合計
        period_expired_grants = db.query(models.LeaveGrant).filter(
            and_(
                models.LeaveGrant.employee_id == emp.id,
                models.LeaveGrant.expire_date >= start_date,
                models.LeaveGrant.expire_date <= end_date
            )
        ).all()
        period_expired = sum(g.days for g in period_expired_grants)

        # 現在のサマリー
        summary = services.get_employee_summary(db, emp.id)

        # 直近付与日
        latest_grant = db.query(models.LeaveGrant).filter(
            models.LeaveGrant.employee_id == emp.id
        ).order_by(models.LeaveGrant.grant_date.desc()).first()
        latest_grant_date = latest_grant.grant_date if latest_grant else ""

        writer.writerow([
            emp.employee_code,
            emp.name,
            emp.hire_date.isoformat(),
            "在籍" if emp.active else "退職",
            float(period_granted),
            float(period_taken),
            float(period_expired),
            float(summary["remaining"]),
            latest_grant_date.isoformat() if latest_grant_date else "",
            summary["next_expiry_date"].isoformat() if summary["next_expiry_date"] else "",
            float(summary["next_expiry_days"])
        ])

    # レスポンスを返す
    output.seek(0)
    filename = f"paid_leave_report_{start_date}_{end_date}.csv"

    # UTF-8 BOMを付けてExcelで正しく開けるようにする
    csv_content = '\ufeff' + output.getvalue()

    return StreamingResponse(
        iter([csv_content.encode('utf-8')]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/generate-all-grants")
async def generate_all_grants(db: Session = Depends(get_db)):
    """全従業員の付与を自動生成"""
    from fastapi.responses import RedirectResponse

    result = services.generate_grants_for_all(db)

    return RedirectResponse(url="/employees/", status_code=303)
