#!/bin/bash
echo "============================================"
echo "  PS AI Agent — Запуск системы"
echo "============================================"
echo ""

# Проверка Node.js
if ! command -v node &> /dev/null; then
    echo "[ОШИБКА] Node.js не установлен!"
    echo "Установите: https://nodejs.org"
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python3 не установлен!"
    echo "Установите: https://python.org"
    exit 1
fi

# Сборка фронтенда
echo "[1/3] Сборка фронтенда..."
npm run build
if [ $? -ne 0 ]; then
    echo "[ОШИБКА] Не удалось собрать фронтенд!"
    exit 1
fi

# Установка Python зависимостей
echo "[2/3] Установка Python зависимостей..."
cd backend
pip3 install -r requirements.txt --quiet

# Запуск бэкенда
echo "[3/3] Запуск сервера..."
echo ""
echo "============================================"
echo "  Откройте: http://localhost:8000"
echo "============================================"
echo ""
python3 main.py
