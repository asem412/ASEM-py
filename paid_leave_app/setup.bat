@echo off
chcp 65001
echo ========================================
echo 有給管理システム - 初回セットアップ
echo ========================================
echo.

REM Pythonバージョン確認
echo [1/5] Pythonバージョンを確認しています...
python --version
if errorlevel 1 (
    echo エラー: Pythonがインストールされていません
    pause
    exit /b 1
)
echo.

REM 仮想環境作成
echo [2/5] 仮想環境を作成しています...
python -m venv venv
if errorlevel 1 (
    echo エラー: 仮想環境の作成に失敗しました
    pause
    exit /b 1
)
echo.

REM 仮想環境有効化
echo [3/5] 仮想環境を有効化しています...
call venv\Scripts\activate.bat
echo.

REM パッケージインストール
echo [4/5] 依存パッケージをインストールしています...
pip install -r requirements.txt
if errorlevel 1 (
    echo エラー: パッケージのインストールに失敗しました
    pause
    exit /b 1
)
echo.

REM データベース初期化
echo [5/5] データベースを初期化しています...
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
if errorlevel 1 (
    echo エラー: データベースの初期化に失敗しました
    pause
    exit /b 1
)
echo.

echo ========================================
echo セットアップが完了しました！
echo ========================================
echo.
echo 次回からは start.bat をダブルクリックして起動してください。
echo.
pause
