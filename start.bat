@echo off
echo ============================================
echo   PS AI Agent — Автономная система
echo   Siemens Plant Simulation 2404
echo   ТЗ v1.0
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

echo [1/3] Сборка фронтенда...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось собрать фронтенд!
    pause
    exit /b 1
)

echo [2/3] Установка Python зависимостей...
cd backend
pip install -r requirements.txt --quiet
cd ..

echo [3/3] Запуск сервера...
echo.
echo ============================================
echo   Откройте: http://localhost:7860
echo ============================================
echo.

echo Выберите режим:
echo   1. Веб-интерфейс (UI)
echo   2. CLI: Полный цикл
echo   3. CLI: Dry-run (без COM)
echo   4. CLI: Selftest
echo.
set /p choice="Ваш выбор (1-4): "

if "%choice%"=="1" (
    cd backend
    python main.py
) else if "%choice%"=="2" (
    set /p desc="Описание линии: "
    python plant_agent_full.py "%desc%" model.spp
) else if "%choice%"=="3" (
    set /p desc="Описание линии: "
    python plant_agent_full.py --dry-run "%desc%"
) else if "%choice%"=="4" (
    python plant_agent_full.py --selftest
) else (
    echo Неверный выбор
)

pause
