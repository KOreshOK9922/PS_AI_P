@echo off
chcp 65001 >nul
echo ============================================
echo   PS AI Agent v2.0 — Установка для Windows
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

echo [1/6] Проверка Python...
python --version
echo.

REM Проверка Node.js
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Node.js не установлен!
    echo Скачайте: https://nodejs.org/
    pause
    exit /b 1
)

echo [2/6] Проверка Node.js...
node --version
echo.

REM Настройка PowerShell
echo [3/6] Настройка PowerShell...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"
echo PowerShell настроен
echo.

REM Установка Python зависимостей
echo [4/6] Установка Python зависимостей...
cd backend
pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ПРЕДУПРЕЖДЕНИЕ] Ошибка установки зависимостей
    echo Пробуем установить pywin32 отдельно...
    pip install pywin32
)
cd ..
echo.

REM Установка Node.js зависимостей
echo [5/6] Установка Node.js зависимостей...
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось установить npm пакеты
    pause
    exit /b 1
)
echo.

REM Сборка фронтенда
echo [6/6] Сборка фронтенда...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось собрать фронтенд
    pause
    exit /b 1
)
echo.

echo ============================================
echo   Установка завершена успешно!
echo ============================================
echo.
echo Следующие шаги:
echo 1. Установите Ollama: https://ollama.com/download
echo 2. Загрузите модель: ollama pull qwen2.5-coder:7b
echo 3. Запустите Plant Simulation 2404
echo 4. Запустите систему: start_server.bat
echo.
pause
