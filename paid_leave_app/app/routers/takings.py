"""
取得実績ルーター
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/takings", tags=["takings"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/new", response_class=HTMLResponse)
async def new_taking_form(
    request: Request,
    employee_id: int = None,
    db: Session = Depends(get_db)
):
    """取得実績登録フォーム"""
    employees = crud.get_employees(db, active_only=True)

    return templates.TemplateResponse(
        "takings/form.html",
        {
            "request": request,
            "taking": None,
            "employees": employees,
            "selected_employee_id": employee_id,
            "kinds": ["全日", "午前休", "午後休"]
        }
    )


@router.post("/")
async def create_taking(
    employee_id: int = Form(...),
    date_val: date = Form(..., alias="date"),
    kind: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    """取得実績を作成"""
    taking = schemas.LeaveTakingCreate(
        employee_id=employee_id,
        date=date_val,
        kind=kind,
        note=note if note else None
    )

    created = crud.create_taking(db, taking)
    if not created:
        raise HTTPException(
            status_code=400,
            detail="有給残日数が不足しています。付与を確認してください。"
        )

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)


@router.get("/{taking_id}/edit", response_class=HTMLResponse)
async def edit_taking_form(
    request: Request,
    taking_id: int,
    db: Session = Depends(get_db)
):
    """取得実績編集フォーム"""
    taking = crud.get_taking(db, taking_id)
    if not taking:
        raise HTTPException(status_code=404, detail="取得実績が見つかりません")

    employees = crud.get_employees(db, active_only=True)

    return templates.TemplateResponse(
        "takings/form.html",
        {
            "request": request,
            "taking": taking,
            "employees": employees,
            "selected_employee_id": taking.employee_id,
            "kinds": ["全日", "午前休", "午後休"]
        }
    )


@router.post("/{taking_id}")
async def update_taking(
    taking_id: int,
    date_val: date = Form(..., alias="date"),
    kind: str = Form(...),
    note: str = Form(""),
    db: Session = Depends(get_db)
):
    """取得実績を更新"""
    # 従業員IDを取得
    existing = crud.get_taking(db, taking_id)
    if not existing:
        raise HTTPException(status_code=404, detail="取得実績が見つかりません")

    taking = schemas.LeaveTakingUpdate(
        date=date_val,
        kind=kind,
        note=note if note else None
    )

    updated = crud.update_taking(db, taking_id, taking)
    if not updated:
        raise HTTPException(
            status_code=400,
            detail="有給残日数が不足しています。"
        )

    return RedirectResponse(url=f"/employees/{existing.employee_id}", status_code=303)


@router.post("/{taking_id}/delete")
async def delete_taking(
    taking_id: int,
    db: Session = Depends(get_db)
):
    """取得実績を削除"""
    # 従業員IDを取得
    existing = crud.get_taking(db, taking_id)
    if not existing:
        raise HTTPException(status_code=404, detail="取得実績が見つかりません")

    employee_id = existing.employee_id

    success = crud.delete_taking(db, taking_id)
    if not success:
        raise HTTPException(status_code=404, detail="取得実績が見つかりません")

    return RedirectResponse(url=f"/employees/{employee_id}", status_code=303)
