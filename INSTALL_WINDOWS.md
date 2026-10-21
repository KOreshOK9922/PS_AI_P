# Инструкция по установке PS AI Agent v2.0 для Windows

## ⚠️ Решение проблем с установкой

### Проблема 1: PowerShell блокирует npm
**Ошибка:** `Невозможно загрузить файл npm.ps1, так как выполнение сценариев отключено`

**Решение:**
```powershell
# Запустите PowerShell от имени администратора и выполните:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Подтвердите изменение: Y (Да)
```

### Проблема 2: pywin32==306 не найден
**Ошибка:** `Could not find a version that satisfies the requirement pywin32==306`

**Решение:**
```powershell
# Установите последнюю версию pywin32:
pip install pywin32

# Или используйте обновленный requirements.txt (уже исправлен)
pip install -r backend\requirements.txt
```

### Проблема 3: requirements.txt не найден
**Ошибка:** `Could not open requirements file: [Errno 2] No such file or directory`

**Решение:**
```powershell
# Перейдите в папку backend перед установкой:
cd backend
pip install -r requirements.txt
```

---

## 📋 Полная инструкция по установке

### Шаг 1: Клонирование репозитория

```powershell
# Откройте PowerShell и выполните:
git clone https://github.com/KOreshOK9922/PS_AI_P.git
cd PS_AI_P
```

### Шаг 2: Настройка PowerShell для npm

```powershell
# Разрешите выполнение скриптов (если еще не сделано):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Введите Y для подтверждения
```

### Шаг 3: Установка Python зависимостей

```powershell
# Перейдите в папку backend:
cd backend

# Установите зависимости:
pip install -r requirements.txt

# Если возникла ошибка с pywin32, установите отдельно:
pip install pywin32
```

### Шаг 4: Установка Node.js зависимостей

```powershell
# Вернитесь в корневую папку:
cd ..

# Установите npm пакеты:
npm install
```

### Шаг 5: Установка Ollama и модели

```powershell
# 1. Скачайте Ollama: https://ollama.com/download
# 2. Установите Ollama
# 3. Загрузите модель:
ollama pull qwen2.5-coder:7b
```

### Шаг 6: Сборка фронтенда

```powershell
# Соберите React приложение:
npm run build
```

### Шаг 7: Запуск системы

```powershell
# Запустите бэкенд:
cd backend
python main.py

# Откройте браузер: http://localhost:7860
```

---

## 🔧 Альтернативный способ установки (batch файл)

Создайте файл `install_windows.bat` в корневой папке:

```batch
@echo off
echo ============================================
echo   PS AI Agent — Установка для Windows
echo ============================================
echo.

echo [1/5] Настройка PowerShell...
powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force"

echo [2/5] Установка Python зависимостей...
cd backend
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Ошибка установки Python зависимостей
    echo Попробуйте: pip install pywin32
    pause
    exit /b 1
)
cd ..

echo [3/5] Установка Node.js зависимостей...
call npm install
if %ERRORLEVEL% neq 0 (
    echo Ошибка установки npm
    pause
    exit /b 1
)

echo [4/5] Сборка фронтенда...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo Ошибка сборки
    pause
    exit /b 1
)

echo [5/5] Установка завершена!
echo.
echo ============================================
echo   Теперь запустите:
echo   cd backend
echo   python main.py
echo ============================================
pause
```

---

## 🚀 Быстрый запуск после установки

### Вариант 1: Через PowerShell

```powershell
cd PS_AI_P\backend
python main.py
```

### Вариант 2: Через batch файл

Создайте `start_windows.bat`:

```batch
@echo off
echo Запуск PS AI Agent...
cd backend
python main.py
pause
```

### Вариант 3: Через Python напрямую

```powershell
python PS_AI_P\backend\main.py
```

---

## 📊 Проверка установки

### Проверка Python зависимостей

```powershell
pip list | findstr fastapi
pip list | findstr pywin32
pip list | findstr psutil
```

### Проверка Node.js

```powershell
node --version
npm --version
```

### Проверка Ollama

```powershell
ollama list
# Должна показать: qwen2.5-coder:7b
```

### Проверка Plant Simulation

```powershell
# Проверьте что Plant Simulation 2404 запущен
tasklist | findstr PlantSimulation
```

---

## 🐛 Решение частых проблем

### Проблема: `ModuleNotFoundError: No module named 'fastapi'`

**Решение:**
```powershell
cd backend
pip install -r requirements.txt
```

### Проблема: `npm: command not found`

**Решение:**
1. Установите Node.js: https://nodejs.org/
2. Перезапустите PowerShell
3. Проверьте: `node --version`

### Проблема: `ollama: command not found`

**Решение:**
1. Установите Ollama: https://ollama.com/download
2. Перезапустите PowerShell
3. Загрузите модель: `ollama pull qwen2.5-coder:7b`

### Проблема: `Plant Simulation не подключается`

**Решение:**
1. Запустите Plant Simulation 2404
2. Проверьте что COM интерфейс зарегистрирован
3. Попробуйте перезапустить PS

### Проблема: `Port 7860 already in use`

**Решение:**
```powershell
# Найдите процесс использующий порт:
netstat -ano | findstr :7860

# Убейте процесс (замените PID):
taskkill /F /PID <PID>
```

---

## 📁 Структура проекта после клонирования

```
PS_AI_P/
├── backend/
│   ├── main.py                 # FastAPI сервер
│   ├── plant_sim.py            # Подключение к PS
│   ├── parallel_agents.py      # Агенты
│   ├── knowledge_base.py       # База знаний
│   └── requirements.txt        # Python зависимости
├── src/
│   └── App.tsx                 # React фронтенд
├── dist/                       # Собранный фронтенд (после npm run build)
├── package.json                # Node.js зависимости
├── README.md                   # Документация
└── INSTALL_WINDOWS.md          # Этот файл
```

---

## ✅ Контрольный список установки

- [ ] Git установлен
- [ ] Python 3.10+ установлен
- [ ] Node.js установлен
- [ ] PowerShell настроен (ExecutionPolicy)
- [ ] Репозиторий клонирован
- [ ] Python зависимости установлены (`pip install -r backend\requirements.txt`)
- [ ] Node.js зависимости установлены (`npm install`)
- [ ] Ollama установлен и модель загружена
- [ ] Фронтенд собран (`npm run build`)
- [ ] Plant Simulation 2404 запущен
- [ ] Бэкенд запущен (`python backend\main.py`)
- [ ] Веб-интерфейс доступен на http://localhost:7860

---

## 🎯 Первый запуск

1. Откройте PowerShell
2. Перейдите в папку проекта: `cd PS_AI_P`
3. Запустите бэкенд: `cd backend` → `python main.py`
4. Откройте браузер: http://localhost:7860
5. Введите описание линии, например:
   ```
   Линия: источник заготовок с интервалом 3 минуты, станция обработки 20 секунд, накопитель на 10 мест, сход
   ```
6. Нажмите "▶ Запустить"
7. Наблюдайте за работой агентов!

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи в файле `agent_log.txt`
2. Проверьте консоль PowerShell на ошибки
3. Убедитесь что все зависимости установлены
4. Проверьте что Plant Simulation запущен

---

**Версия:** 2.0  
**Платформа:** Windows 10/11  
**Требования:** Python 3.10+, Node.js 18+, Ollama, Plant Simulation 2404
