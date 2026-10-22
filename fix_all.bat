@echo off
chcp 65001 >nul
echo ============================================
echo   PS AI Agent — Автоматическое исправление
echo ============================================
echo.

REM Проверка что мы в system32
if "%CD%"=="C:\Windows\system32\PS_AI_P" (
    echo [КРИТИЧЕСКАЯ ОШИБКА] Проект находится в системной директории!
    echo.
    echo Будет выполнено перемещение в C:\Projects\PS_AI_P
    echo.
    pause
    
    REM Создаём директорию
    if not exist "C:\Projects" mkdir "C:\Projects"
    
    REM Перемещаем проект
    echo Перемещение проекта...
    move "C:\Windows\system32\PS_AI_P" "C:\Projects\PS_AI_P"
    if %ERRORLEVEL% neq 0 (
        echo [ОШИБКА] Не удалось переместить проект
        echo Попробуйте вручную:
        echo Move-Item -Path "C:\Windows\system32\PS_AI_P" -Destination "C:\Projects\PS_AI_P"
        pause
        exit /b 1
    )
    
    echo.
    echo [УСПЕХ] Проект перемещён в C:\Projects\PS_AI_P
    echo.
    
    REM Переходим в новую директорию
    cd /d "C:\Projects\PS_AI_P"
) else (
    echo Проект уже в корректной директории: %CD%
)

echo.
echo ============================================
echo   Очистка старых зависимостей
echo ============================================
echo.

REM Удаляем старые node_modules
if exist "node_modules" (
    echo Удаление node_modules...
    rmdir /s /q node_modules
)

if exist "package-lock.json" (
    echo Удаление package-lock.json...
    del /f package-lock.json
)

if exist "backend\node_modules" (
    echo Удаление backend\node_modules...
    rmdir /s /q backend\node_modules
)

if exist "backend\venv" (
    echo Удаление backend\venv...
    rmdir /s /q backend\venv
)

echo.
echo ============================================
echo   Создание виртуального окружения
echo ============================================
echo.

cd backend
echo Создание venv...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось создать venv
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Установка зависимостей
echo ============================================
echo.

echo Активация venv...
call venv\Scripts\activate.bat

echo Обновление pip...
python -m pip install --upgrade pip

echo.
echo Установка Python зависимостей...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось установить Python зависимости
    pause
    exit /b 1
)

cd ..

echo.
echo Установка Node.js зависимостей...
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось установить npm зависимости
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Сборка frontend
echo ============================================
echo.

call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ОШИБКА] Не удалось собрать frontend
    pause
    exit /b 1
)

echo.
echo ============================================
echo   ВСЕ ИСПРАВЛЕНИЯ ВЫПОЛНЕНЫ!
echo ============================================
echo.
echo Проект перемещён в: C:\Projects\PS_AI_P
echo Виртуальное окружение создано: backend\venv
echo Зависимости установлены
echo Frontend собран
echo.
echo ============================================
echo   ЗАПУСК СИСТЕМЫ
echo ============================================
echo.
echo Для запуска выполните:
echo   cd C:\Projects\PS_AI_P\backend
echo   venv\Scripts\activate
echo   python main.py
echo.
echo Затем откройте: http://localhost:7860
echo.
pause
