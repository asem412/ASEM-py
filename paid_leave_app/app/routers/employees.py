"""
従業員ルーター
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app import crud, schemas, services
from app.database import get_db

router = APIRouter(prefix="/employees", tags=["employees"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def list_employees(
    request: Request,
    db: Session = Depends(get_db)
):
    """従業員一覧"""
    employees = crud.get_employees(db)

    # 各従業員の残日数を計算
    employees_with_summary = []
    for emp in employees:
        summary = services.get_employee_summary(db, emp.id)
        employees_with_summary.append({
            "employee": emp,
            "remaining": summary["remaining"],
            "next_expiry_date": summary["next_expiry_date"],
            "next_expiry_days": summary["next_expiry_days"]
        })

    return templates.TemplateResponse(
        "employees/list.html",
        {"request": request, "employees": employees_with_summary}
    )


@router.get("/new", response_class=HTMLResponse)
async def new_employee_form(request: Request):
    """従業員登録フォーム"""
    return templates.TemplateResponse(
        "employees/form.html",
        {"request": request, "employee": None}
    )


@router.post("/")
async def create_employee(
    employee_code: str = Form(...),
    name: str = Form(...),
    hire_date: date = Form(...),
    active: bool = Form(True),
    db: Session = Depends(get_db)
):
    """従業員を作成"""
    # 既存チェック
    existing = crud.get_employee_by_code(db, employee_code)
    if existing:
        raise HTTPException(status_code=400, detail="この社員番号は既に使用されています")

    employee = schemas.EmployeeCreate(
        employee_code=employee_code,
        name=name,
        hire_date=hire_date,
        active=active
    )
    crud.create_employee(db, employee)

    return RedirectResponse(url="/employees/", status_code=303)


@router.get("/{employee_id}", response_class=HTMLResponse)
async def employee_detail(
    request: Request,
    employee_id: int,
    db: Session = Depends(get_db)
):
    """従業員詳細"""
    employee = crud.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="従業員が見つかりません")

    # サマリー取得
    summary = services.get_employee_summary(db, employee_id)

    # 付与一覧（残日数付き）
    grants_with_remaining = []
    for grant, remaining in summary["grants"]:
        used = grant.days - remaining
        grants_with_remaining.append({
            "grant": grant,
            "used": used,
            "remaining": remaining
        })

    # 失効済み付与
    all_grants = crud.get_grants(db, employee_id)
    expired_grants = [g for g in all_grants if g.expire_date <= date.today()]

    # 取得一覧
    takings = crud.get_takings(db, employee_id)

    # 取得履歴を年別にグループ化
    takings_by_year = {}
    for taking in takings:
        year = taking.date.year
        if year not in takings_by_year:
            takings_by_year[year] = []
        takings_by_year[year].append(taking)

    # 年を降順にソート
    sorted_years = sorted(takings_by_year.keys(), reverse=True)

    return templates.TemplateResponse(
        "employees/detail.html",
        {
            "request": request,
            "employee": employee,
            "summary": summary,
            "grants": grants_with_remaining,
            "expired_grants": expired_grants,
            "takings": takings,
            "takings_by_year": takings_by_year,
            "sorted_years": sorted_years
        }
    )


@router.get("/{employee_id}/edit", response_class=HTMLResponse)
async def edit_employee_form(
    request: Request,
    employee_id: int,
    db: Session = Depends(get_db)
):
    """従業員編集フォーム"""
    employee = crud.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="従業員が見つかりません")

    return templates.TemplateResponse(
        "employees/form.html",
        {"request": request, "employee": employee}
    )


@router.post("/{employee_id}")
async def update_employee(
    employee_id: int,
    employee_code: str = Form(...),
    name: str = Form(...),
    hire_date: date = Form(...),
    active: bool = Form(True),
    db: Session = Depends(get_db)
):
    """従業員を更新"""
    employee = schemas.EmployeeUpdate(
        employee_code=employee_code,
        name=name,
        hire_date=hire_date,
        active=active
    )
    updated = crud.update_employee(db, employee_id, employee)
    if not updated:
        raise HTTPException(status_code=404, detail="従業員が見つかりません")

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)


@router.post("/{employee_id}/generate-grants")
async def generate_grants(
    employee_id: int,
    db: Session = Depends(get_db)
):
    """従業員の付与を自動生成"""
    employee = crud.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="従業員が見つかりません")

    count = services.generate_grants_for_employee(db, employee)

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)


@router.get("/{employee_id}/grants/new", response_class=HTMLResponse)
async def new_grant_form(
    request: Request,
    employee_id: int,
    db: Session = Depends(get_db)
):
    """付与追加フォーム"""
    employee = crud.get_employee(db, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="従業員が見つかりません")

    return templates.TemplateResponse(
        "grants/form.html",
        {"request": request, "employee": employee, "grant": None}
    )


@router.post("/{employee_id}/grants")
async def create_grant(
    employee_id: int,
    grant_date: date = Form(...),
    days: float = Form(...),
    expire_date: date = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    """付与を作成"""
    from decimal import Decimal
    from app import models

    grant = models.LeaveGrant(
        employee_id=employee_id,
        grant_date=grant_date,
        days=Decimal(str(days)),
        expire_date=expire_date,
        note=note if note else None
    )
    db.add(grant)
    db.commit()

    # 取得実績を再計算（新しい付与が追加されたため）
    services.recalculate_usages_for_employee(db, employee_id)

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)


@router.get("/grants/{grant_id}/edit", response_class=HTMLResponse)
async def edit_grant_form(
    request: Request,
    grant_id: int,
    db: Session = Depends(get_db)
):
    """付与編集フォーム"""
    from app import models

    grant = db.query(models.LeaveGrant).filter(models.LeaveGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="付与が見つかりません")

    employee = crud.get_employee(db, grant.employee_id)

    return templates.TemplateResponse(
        "grants/form.html",
        {"request": request, "employee": employee, "grant": grant}
    )


@router.post("/grants/{grant_id}")
async def update_grant(
    grant_id: int,
    grant_date: date = Form(...),
    days: float = Form(...),
    expire_date: date = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    """付与を更新"""
    from decimal import Decimal
    from app import models

    grant = db.query(models.LeaveGrant).filter(models.LeaveGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="付与が見つかりません")

    employee_id = grant.employee_id

    grant.grant_date = grant_date
    grant.days = Decimal(str(days))
    grant.expire_date = expire_date
    grant.note = note if note else None

    db.commit()

    # 取得実績を再計算
    services.recalculate_usages_for_employee(db, employee_id)

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)


@router.post("/grants/{grant_id}/delete")
async def delete_grant(
    grant_id: int,
    db: Session = Depends(get_db)
):
    """付与を削除"""
    from app import models

    grant = db.query(models.LeaveGrant).filter(models.LeaveGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="付与が見つかりません")

    employee_id = grant.employee_id

    # この付与に紐づく消化明細を削除
    db.query(models.LeaveUsage).filter(models.LeaveUsage.grant_id == grant_id).delete()

    # 付与を削除
    db.delete(grant)
    db.commit()

    # 取得実績を再計算
    services.recalculate_usages_for_employee(db, employee_id)

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)
