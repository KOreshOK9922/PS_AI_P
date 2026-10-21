# 🚀 Установка и запуск

## Требования

- **Python 3.10+**
- **Node.js 18+**
- **Ollama** с моделью `qwen2.5-coder:7b` или `qwen2.5-coder:14b`

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd multi-agent-system
```

### 2. Установка Python зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 3. Установка Node.js зависимостей

```bash
cd ..
npm install
```

### 4. Установка Ollama

**Windows/Linux/macOS:**
```bash
# Скачайте с https://ollama.com/download
# Установите и загрузите модель:
ollama pull qwen2.5-coder:7b
```

**Рекомендуемые модели:**
- `qwen2.5-coder:7b` - базовая (8GB RAM)
- `qwen2.5-coder:14b` - улучшенная (16GB RAM)
- `qwen2.5-coder:32b` - максимальная (32GB RAM)

### 5. Сборка frontend

```bash
npm run build
```

## Запуск

### Вариант 1: Через Python (рекомендуется)

```bash
cd backend
python main.py
```

Откройте браузер: **http://localhost:8000**

### Вариант 2: Автоматический запуск

**Windows:**
```bash
start.bat
```

**Linux/macOS:**
```bash
bash start.sh
```

## Проверка работы

### 1. Проверьте backend

```bash
curl http://localhost:8000/health
```

Должен вернуть:
```json
{"status":"ok","ollama":true,"active_tasks":0}
```

### 2. Проверьте Ollama

```bash
ollama list
```

Должна показать загруженную модель.

### 3. Откройте веб-интерфейс

Откройте **http://localhost:8000** в браузере.

## Первый запуск

1. Введите требование, например:
   ```
   Создай REST API для управления пользователями с регистрацией и авторизацией
   ```

2. Нажмите **"▶ Запустить"**

3. Наблюдайте за работой 7 агентов:
   - 🎯 Orchestrator - координирует работу
   - 📊 Product Analyst - анализирует требования
   - 🏛️ System Architect - проектирует архитектуру
   - 💻 Lead Engineer - реализует код
   - 🧪 QA Engineer - тестирует
   - 🔍 Code Reviewer - ревьюит
   - 🚀 DevOps Engineer - упаковывает

4. Просматривайте артефакты во вкладке **"📦 Артефакты"**

## Решение проблем

### Проблема: Ollama не отвечает

**Решение:**
```bash
# Проверьте что Ollama запущена
ollama list

# Если модель не загружена:
ollama pull qwen2.5-coder:7b

# Перезапустите Ollama service
# Windows: Перезапустите службу Ollama
# Linux: sudo systemctl restart ollama
```

### Проблема: Порт 8000 занят

**Решение:**
```bash
# Найдите процесс
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/macOS

# Убейте процесс
taskkill /F /PID <PID>        # Windows
kill -9 <PID>                 # Linux/macOS
```

### Проблема: Модули не найдены

**Решение:**
```bash
cd backend
pip install -r requirements.txt --force-reinstall
```

### Проблема: Frontend не загружается

**Решение:**
```bash
# Пересоберите frontend
npm run build

# Проверьте что dist папка существует
ls dist  # Linux/macOS
dir dist  # Windows
```

## Конфигурация

### Изменение модели LLM

Отредактируйте `backend/llm_client.py`:
```python
def __init__(self, url: str = "http://localhost:11434", model: str = "qwen2.5-coder:14b"):
```

### Изменение порта

Отредактируйте `backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=9000)  # Измените порт
```

### Изменение лимита итераций

В веб-интерфейсе или через API:
```json
{
  "requirement": "...",
  "max_iterations": 5
}
```

## API Документация

### POST /api/run

Запуск задачи:
```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Создай REST API",
    "max_iterations": 3
  }'
```

### GET /api/status/{task_id}

Статус задачи:
```bash
curl http://localhost:8000/api/status/{task_id}
```

### GET /api/logs/{task_id}

Логи задачи:
```bash
curl http://localhost:8000/api/logs/{task_id}
```

### GET /api/artifacts/{task_id}

Артефакты задачи:
```bash
curl http://localhost:8000/api/artifacts/{task_id}
```

## Производительность

### Требования к системе

**Минимальные:**
- CPU: 4 ядра
- RAM: 16GB
- Disk: 10GB
- GPU: не требуется (CPU inference)

**Рекомендуемые:**
- CPU: 8+ ядер
- RAM: 32GB
- Disk: 20GB
- GPU: NVIDIA с 8GB+ VRAM (опционально)

### Время выполнения

- **Анализ требований:** 10-30 секунд
- **Проектирование архитектуры:** 20-60 секунд
- **Реализация кода:** 30-120 секунд
- **Тестирование:** 20-60 секунд
- **Ревью:** 15-45 секунд
- **Упаковка:** 10-30 секунд

**Общее время:** 2-6 минут на задачу

## Поддержка

Если возникли проблемы:

1. Проверьте логи в консоли
2. Проверьте файл `agent_log.txt`
3. Убедитесь что все зависимости установлены
4. Перезапустите систему

## Обновление

```bash
git pull
cd backend
pip install -r requirements.txt --upgrade
cd ..
npm install
npm run build
```

---

**Готово к использованию!** 🚀
