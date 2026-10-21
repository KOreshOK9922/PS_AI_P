# 🏗️ Архитектура PS AI Agent v3.0

## ✅ Правильная архитектура для Plant Simulation 2404

Система специализирована **исключительно** на автоматизации работы с Siemens Plant Simulation 2404.

---

## 🎯 Цель системы

**Автоматическое построение моделей производственных линий в Plant Simulation 2404 по текстовому описанию.**

Пример:
```
Ввод: "Линия: источник заготовок с интервалом 3 минуты, 
       станция обработки 20 секунд, накопитель на 10 мест, сход"

Результат: Готовая модель .spp с объектами Source → Station → Buffer → Drain,
           соединёнными коннекторами, с настроенными параметрами
```

---

## 🤖 Роли агентов (специализация на Plant Simulation)

### 1. 🎯 Orchestrator (Оркестратор)
**Роль:** Координирует весь цикл построения модели в PS

**Ответственность:**
- Управление последовательностью фаз
- Контроль итераций отладки (макс. 3)
- Принятие решений при ошибках
- Финальная проверка результата

**Взаимодействие с PS:** Нет прямого взаимодействия — только координация

---

### 2. 🏗️ Architect Agent (Архитектор)
**Роль:** Парсит текстовое описание → JSON-спецификация модели

**Ответственность:**
- Извлечение типов объектов (Source, Station, Buffer, Drain)
- Определение параметров (interval, procTime, capacity)
- Установление порядка соединений
- Использование LLM (Ollama) или fallback regex-парсера

**Вход:** Текстовое описание на русском/английском  
**Выход:** JSON-спецификация:
```json
{
  "objects": [
    {"name": "SRC_1", "class": "Source", "x": 100, "y": 100, "params": {"interval": 180}},
    {"name": "ST_1", "class": "Station", "x": 220, "y": 100, "params": {"procTime": 20}},
    {"name": "BUF_1", "class": "Buffer", "x": 340, "y": 100, "params": {"capacity": 10}},
    {"name": "DRN_1", "class": "Drain", "x": 460, "y": 100, "params": {}}
  ],
  "connections": [["SRC_1", "ST_1"], ["ST_1", "BUF_1"], ["BUF_1", "DRN_1"]]
}
```

**Взаимодействие с PS:** Нет — только парсинг текста

---

### 3. 🔨 Builder Agent (Строитель)
**Роль:** Генерирует SimTalk код из JSON-спецификации

**Ответственность:**
- Генерация кода создания объектов через `createObject(f, x, y)`
- Генерация кода соединений через `Connector.connect(obj1, obj2)`
- Генерация кода установки параметров
- Использование базы знаний для выбора правильных методов

**Вход:** JSON-спецификация  
**Выход:** SimTalk код:
```simtalk
var f : object
f := .Models.Model

var SRC_1 : object
SRC_1 := .MaterialFlow.Source.createObject(f, 100, 100)
SRC_1.setName("SRC_1")

var ST_1 : object
ST_1 := .MaterialFlow.Station.createObject(f, 220, 100)
ST_1.setName("ST_1")

f.SRC_1.interval := 180
f.ST_1.procTime := 20

.MaterialFlow.Connector.connect(f.SRC_1, f.ST_1)
```

**Взаимодействие с PS:** Нет — только генерация кода

---

### 4. ⚡ Executor Agent (Исполнитель)
**Роль:** Выполняет SimTalk код в Plant Simulation

**Ответственность:**
- Подключение к PS через COM/REST/Python Interface
- Создание новой модели
- Выполнение сгенерированного кода
- Обработка ошибок выполнения

**Вход:** SimTalk код  
**Выход:** Результат выполнения (успех/ошибка)

**Взаимодействие с PS:** **ПРЯМОЕ** — выполняет код через COM-интерфейс

**Методы подключения:**
1. **COM/DCOM** — `ExecuteSimTalk(code)`
2. **REST API** — POST запрос к PS
3. **Python Interface** — встроенный Python в PS 2404

---

### 5. 🐛 Debugger Agent (Отладчик)
**Роль:** Анализирует ошибки COM и ищет решения

**Ответственность:**
- Анализ текста ошибки
- Поиск похожих ошибок в базе знаний
- Генерация исправленного кода
- Предложение альтернативных методов

**Вход:** Текст ошибки + исходный код  
**Выход:** Исправленный код или список альтернатив

**Взаимодействие с PS:** Нет — только анализ ошибок

**Пример:**
```
Ошибка: "Unknown identifier 'connect'"
Решение: Заменить на ".MaterialFlow.Connector.connect(obj1, obj2)"
```

---

### 6. 🔬 Researcher Agent (Исследователь)
**Роль:** Тестирует методы API Plant Simulation

**Ответственность:**
- Параллельное тестирование методов создания объектов
- Тестирование методов соединений
- Интроспекция атрибутов объектов
- Накопление знаний о рабочем API

**Вход:** Задача исследования (full/connections/classes)  
**Выход:** Отчёт о рабочих/нерабочих методах

**Взаимодействие с PS:** **ПРЯМОЕ** — тестирует методы через COM

**Пример тестируемых методов:**
```python
# Создание объектов
.MaterialFlow.Source.createObject(f, x, y)  # ✅ Работает
.MaterialFlow.Source.derive(root)            # ❌ Устарело

# Соединения
.MaterialFlow.Connector.connect(obj1, obj2)  # ✅ Работает
obj1.succ := obj2                            # ❌ Read-only
obj1.connect(obj2)                           # ❌ Не существует
```

---

### 7. ✅ Validator Agent (Валидатор)
**Роль:** Проверяет корректность созданной модели

**Ответственность:**
- Подсчёт созданных объектов
- Проверка наличия соединений
- Валидация параметров
- Сравнение с исходной спецификацией

**Вход:** JSON-спецификация + ссылка на модель в PS  
**Выход:** Отчёт о валидации (пройдена/не пройдена)

**Взаимодействие с PS:** **ПРЯМОЕ** — читает данные из модели через COM

**Пример проверки:**
```python
# Создаём DataTable для подсчёта
var dt : object
dt := .InformationFlow.DataTable.createObject(f, "VALIDATION")
dt.setCell(1, 1, f.numObjects)

# Читаем количество объектов
actual_count = app.GetTableCell(".Models.Model.VALIDATION", 1, 1)
expected_count = len(spec["objects"])

if actual_count == expected_count:
    print("✅ Валидация пройдена")
```

---

## 🔄 Workflow (последовательность выполнения)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Пользователь вводит текстовое описание                  │
│     "Источник 3 мин, станция 20 сек, буфер 10, сход"       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Orchestrator запускает Architect Agent                  │
│     Architect парсит текст → JSON-спецификация              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Orchestrator запускает Builder Agent                    │
│     Builder генерирует SimTalk код из JSON                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Orchestrator запускает Executor Agent                   │
│     Executor выполняет код в Plant Simulation               │
│                                                              │
│     ┌──────────────────────────────────────────────────┐   │
│     │  Если ошибка:                                    │   │
│     │  → Debugger Agent анализирует ошибку             │   │
│     │  → Debugger предлагает исправление               │   │
│     │  → Executor повторяет попытку (макс. 3 раза)     │   │
│     └──────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Orchestrator запускает Validator Agent                  │
│     Validator проверяет корректность модели                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Orchestrator сохраняет модель в .spp                    │
│     "model.spp"                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗄️ База знаний (Knowledge Base)

SQLite база данных для накопления опыта работы с Plant Simulation API.

### Таблицы:

1. **api_methods** — методы API с статистикой успешности
   ```
   method_name | code_template | success_rate | attempts | successes
   ```

2. **error_patterns** — шаблоны ошибок и решения
   ```
   error_message | solution | frequency | last_seen
   ```

3. **object_classes** — классы объектов PS
   ```
   class_name | create_method | required_params | verified
   ```

4. **working_solutions** — рабочие решения задач
   ```
   task_description | solution_code | success_count
   ```

### Как используется:

- **Builder** — получает информацию о классах из `object_classes`
- **Debugger** — ищет решения в `error_patterns`
- **Researcher** — записывает результаты тестирования в `api_methods`

---

## 🔌 Подключение к Plant Simulation

### Метод 1: COM/DCOM (основной)
```python
import win32com.client
app = win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl")
app.ExecuteSimTalk(code)
```

### Метод 2: REST API (экспериментальный)
```python
import httpx
response = httpx.post("http://localhost:7860/api/execute", json={"code": code})
```

### Метод 3: Python Interface (PS 2404+)
```simtalk
var py : object
py := .Python.createObject(f, 100, 100)
py.sourceCode := "print('Hello from PS!')"
py.execute()
```

### Автоматическое определение
Система автоматически пробует все методы и выбирает доступный.

---

## 📊 Подтверждённые рабочие методы API (PS 2404)

| Метод | Статус | Пример |
|-------|--------|--------|
| `createObject(f, x, y)` | ✅ Работает | `.MaterialFlow.Source.createObject(f, 100, 100)` |
| `Connector.connect(obj1, obj2)` | ✅ Работает | `.MaterialFlow.Connector.connect(src, dst)` |
| `setName("name")` | ✅ Работает | `obj.setName("SRC_1")` |
| `deleteObject` | ✅ Работает | `obj.deleteObject` |
| Установка параметров | ✅ Работает | `f.SRC_1.interval := 180` |
| `derive(root)` | ❌ Устарело | Используйте `createObject` |
| `obj.succ := obj2` | ❌ Read-only | Используйте `Connector.connect` |
| `SingleProc` | ❌ Не существует | Используйте `Station` |

---

## 🎯 Критерии успешности

Система работает корректно, если:

1. ✅ Принимает текстовое описание на русском/английском
2. ✅ Генерирует JSON-спецификацию с объектами PS
3. ✅ Генерирует валидный SimTalk код
4. ✅ Выполняет код в Plant Simulation через COM
5. ✅ Создаёт объекты Source, Station, Buffer, Drain
6. ✅ Соединяет объекты через `Connector.connect()`
7. ✅ Устанавливает параметры (interval, procTime, capacity)
8. ✅ Сохраняет модель в .spp файл
9. ✅ При ошибках — автоматически отлаживает (до 3 итераций)
10. ✅ Накапливает знания о рабочем API в базе данных

---

## 📁 Структура проекта

```
PS_AI_P/
├── backend/
│   ├── main.py              # FastAPI сервер (API + frontend)
│   ├── orchestrator.py      # Оркестратор для PS
│   ├── parallel_agents.py   # 7 агентов для PS
│   ├── plant_sim.py         # COM-интерфейс к PS 2404
│   ├── knowledge_base.py    # SQLite база знаний
│   └── requirements.txt     # Python зависимости
├── src/
│   └── App.tsx              # React frontend
├── dist/                    # Собранный frontend
├── plant_agent_full.py      # CLI версия
├── index.html
├── package.json
└── README.md
```

---

## 🚀 Запуск

```bash
# 1. Установить зависимости
cd backend
pip install -r requirements.txt
cd ..
npm install

# 2. Установить Ollama (опционально)
ollama pull qwen2.5-coder:7b

# 3. Запустить Plant Simulation 2404

# 4. Запустить backend
cd backend
python main.py

# 5. Открыть браузер
# http://localhost:7860
```

---

## ✅ Итог

**Архитектура полностью соответствует задаче автоматизации Plant Simulation 2404:**

- ✅ Все 7 агентов специализированы на работе с PS
- ✅ Используются правильные методы API PS 2404
- ✅ Есть цикл обратной связи с отладчиком
- ✅ Накапливается база знаний о рабочем API
- ✅ Поддерживаются множественные методы подключения к PS
- ✅ Система полностью автономна после запуска

**Это НЕ мультиагентная система для генерации произвольного кода — это специализированная система для автоматизации Plant Simulation!**
