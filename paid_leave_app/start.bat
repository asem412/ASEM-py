@echo off
chcp 65001
echo ========================================
echo 有給管理システム
echo ========================================
echo.
echo システムを起動しています...
echo.

REM 仮想環境を有効化
call venv\Scripts\activate.bat

REM FastAPIサーバーを起動
echo ブラウザで http://127.0.0.1:8000/ にアクセスしてください
echo.
echo 終了するには Ctrl+C を押してください
echo.
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause
