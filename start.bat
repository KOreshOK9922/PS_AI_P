@echo off
echo ============================================
echo   PS AI Agent — Запуск системы
echo ============================================
echo.

REM Проверка Node.js
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Node.js не установлен!
    echo Установите: https://nodejs.org
    pause
    exit /b 1
)

REM Проверка Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Python не установлен!
    echo Установите: https://python.org
    pause
    exit /b 1
)

REM Сборка фронтенда
echo [1/3] Сборка фронтенда...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось собрать фронтенд!
    pause
    exit /b 1
)

REM Установка Python зависимостей
echo [2/3] Установка Python зависимостей...
cd backend
pip install -r requirements.txt --quiet

REM Запуск бэкенда
echo [3/3] Запуск сервера...
echo.
echo ============================================
echo   Откройте: http://localhost:8000
echo ============================================
echo.
python main.py

pause
