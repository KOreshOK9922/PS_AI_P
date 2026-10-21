@echo off
chcp 65001 >nul
echo ============================================
echo   PS AI Agent — Диагностика системы
echo ============================================
echo.

echo [1/7] Проверка Python...
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python --version
    echo [OK] Python установлен
) else (
    echo [ОШИБКА] Python не установлен!
    echo Скачайте: https://www.python.org/downloads/
)
echo.

echo [2/7] Проверка Node.js...
where node >nul 2>nul
if %ERRORLEVEL% equ 0 (
    node --version
    echo [OK] Node.js установлен
) else (
    echo [ОШИБКА] Node.js не установлен!
    echo Скачайте: https://nodejs.org/
)
echo.

echo [3/7] Проверка npm...
where npm >nul 2>nul
if %ERRORLEVEL% equ 0 (
    npm --version
    echo [OK] npm установлен
) else (
    echo [ОШИБКА] npm не установлен!
)
echo.

echo [4/7] Проверка Ollama...
where ollama >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Ollama модели:
    ollama list
    echo [OK] Ollama установлен
) else (
    echo [ОШИБКА] Ollama не установлен!
    echo Скачайте: https://ollama.com/download
)
echo.

echo [5/7] Проверка Plant Simulation...
tasklist | findstr /I "PlantSimulation" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Plant Simulation запущен
) else (
    echo [ОШИБКА] Plant Simulation не запущен!
    echo Запустите Siemens Plant Simulation 2404
)
echo.

echo [6/7] Проверка Python зависимостей...
pip list | findstr /I "fastapi" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] fastapi установлен
) else (
    echo [ОШИБКА] fastapi не установлен!
    echo Выполните: cd backend ^&^& pip install -r requirements.txt
)

pip list | findstr /I "pywin32" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] pywin32 установлен
) else (
    echo [ОШИБКА] pywin32 не установлен!
    echo Выполните: pip install pywin32
)

pip list | findstr /I "psutil" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] psutil установлен
) else (
    echo [ОШИБКА] psutil не установлен!
)
echo.

echo [7/7] Проверка портов...
netstat -ano | findstr ":7860" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [ВНИМАНИЕ] Порт 7860 уже используется
    echo Возможно сервер уже запущен
) else (
    echo [OK] Порт 7860 свободен
)

netstat -ano | findstr ":11434" >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [OK] Ollama запущена (порт 11434)
) else (
    echo [ОШИБКА] Ollama не запущена!
    echo Запустите Ollama
)
echo.

echo ============================================
echo   Диагностика завершена
echo ============================================
echo.
echo Если все компоненты установлены:
echo 1. cd backend
echo 2. python main.py
echo 3. Откройте: http://localhost:7860
echo.
pause
