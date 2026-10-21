#!/bin/bash

echo "============================================"
echo "  Multi-Agent Code Generation System"
echo "  Запуск системы..."
echo "============================================"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[ОШИБКА] Python3 не установлен!"
    echo "Установите: https://www.python.org/downloads/"
    exit 1
fi

# Проверка Node.js
if ! command -v node &> /dev/null; then
    echo "[ОШИБКА] Node.js не установлен!"
    echo "Установите: https://nodejs.org/"
    exit 1
fi

# Проверка Ollama
if ! command -v ollama &> /dev/null; then
    echo "[ОШИБКА] Ollama не установлен!"
    echo "Установите: https://ollama.com/download"
    exit 1
fi

echo "[1/3] Проверка зависимостей..."
python3 --version
node --version
ollama --version
echo ""

echo "[2/3] Сборка frontend..."
npm run build
if [ $? -ne 0 ]; then
    echo "[ОШИБКА] Не удалось собрать frontend"
    exit 1
fi
echo ""

echo "[3/3] Запуск backend..."
echo ""
echo "============================================"
echo "  Откройте: http://localhost:8000"
echo "============================================"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

cd backend
python3 main.py
