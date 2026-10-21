@echo off
chcp 65001 >nul
echo ============================================
echo   Multi-Agent Code Generation System
echo   Запуск системы...
echo ============================================
echo.

REM Проверка Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Python не установлен!
    echo Скачайте: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Проверка Node.js
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Node.js не установлен!
    echo Скачайте: https://nodejs.org/
    pause
    exit /b 1
)

REM Проверка Ollama
where ollama >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Ollama не установлен!
    echo Скачайте: https://ollama.com/download
    pause
    exit /b 1
)

echo [1/3] Проверка зависимостей...
python --version
node --version
ollama --version
echo.

echo [2/3] Сборка frontend...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось собрать frontend
    pause
    exit /b 1
)
echo.

echo [3/3] Запуск backend...
echo.
echo ============================================
echo   Откройте: http://localhost:8000
echo ============================================
echo.
echo Для остановки нажмите Ctrl+C
echo.

cd backend
python main.py

pause
