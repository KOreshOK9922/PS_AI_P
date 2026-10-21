@echo off
chcp 65001 >nul
echo ============================================
echo   PS AI Agent v2.0 — Запуск сервера
echo ============================================
echo.

REM Проверка Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Python не установлен!
    pause
    exit /b 1
)

REM Проверка наличия backend папки
if not exist "backend\main.py" (
    echo [ОШИБКА] Файл backend\main.py не найден!
    echo Убедитесь что вы находитесь в корневой папке проекта
    pause
    exit /b 1
)

echo Запуск сервера...
echo.
echo ============================================
echo   Откройте браузер: http://localhost:7860
echo ============================================
echo.
echo Для остановки нажмите Ctrl+C
echo.

cd backend
python main.py

pause
