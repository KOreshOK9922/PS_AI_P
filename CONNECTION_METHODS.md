# Варианты подключения к Plant Simulation 2404

## Обзор

Plant Simulation 2404 предоставляет **5 методов подключения** для автоматизации:

1. **COM/DCOM (RemoteControl)** — классический метод
2. **REST API** — новый веб-интерфейс
3. **Python Interface** — встроенный Python в PS 2404
4. **SimTalk через файлы** — выполнение скриптов
5. **Clipboard** — копирование из шаблонов

## 1. COM/DCOM (RemoteControl)

### Описание
Классический метод через Windows COM-интерфейс.

### Подключение
```python
import win32com.client
app = win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl")
app.SetNoMessageBox(True)
```

### Возможности
- ✅ Создание объектов: `createObject(f, x, y)`
- ✅ Соединения: `Connector.connect(obj1, obj2)`
- ✅ Выполнение SimTalk: `ExecuteSimTalk(code)`
- ✅ Сохранение моделей: `SaveModel(path)`
- ✅ Чтение параметров: `GetValue()`

### Ограничения
- Только Windows
- Требует запущенный PS
- Zombie-процессы могут блокировать

### Статус
✅ **Работает** — основной метод системы

---

## 2. REST API

### Описание
Plant Simulation 2404 может предоставлять REST API (зависит от конфигурации).

### Подключение
```python
import httpx
response = httpx.get("http://localhost:7860/api/health")
```

### Возможности
- ✅ Кроссплатформенность
- ✅ Веб-интерфейс
- ✅ Интеграция с другими системами

### Ограничения
- Может быть отключен по умолчанию
- Требует настройки PS

### Статус
⚠️ **Экспериментальный** — проверяется автоматически

---

## 3. Python Interface (встроенный в PS 2404)

### Описание
**НОВАЯ ВОЗМОЖНОСТЬ** в Plant Simulation 2404 — встроенный Python объект.

### Подключение
```python
# Внутри Plant Simulation
python_obj = .Python.createObject(f, x, y)
python_obj.execute()
```

### Возможности
- ✅ Прямой доступ к объектам PS
- ✅ Использование Python библиотек
- ✅ Чтение/запись DataTable
- ✅ Интеграция с AI/ML

### Ограничения
- Только PS 2404+
- Требует настройки внутри PS

### Статус
🔬 **Исследуется** — перспективное направление

### Пример использования
```python
# Создание Python объекта в PS
var py : object
py := .Python.createObject(f, 100, 100)

# Установка кода
py.sourceCode := """
import sys
print("Hello from Plant Simulation!")
"""

# Выполнение
py.execute()
```

---

## 4. SimTalk через файлы

### Описание
Выполнение SimTalk скриптов из файлов.

### Подключение
```python
# Сохранение скрипта
with open("script.txt", "w") as f:
    f.write(simtalk_code)

# Загрузка в PS через COM
app.ExecuteSimTalk('readFile("script.txt")')
```

### Возможности
- ✅ Длинные скрипты
- ✅ Переиспользование кода
- ✅ Версионирование

### Ограничения
- Требует COM для загрузки
- Ограничения файловой системы

### Статус
✅ **Работает** — вспомогательный метод

---

## 5. Clipboard (копирование из шаблонов)

### Описание
Копирование объектов из шаблона через буфер обмена.

### Подключение
```python
# Выделение объектов
app.ExecuteSimTalk('root.Template.Select')

# Копирование
app.ExecuteSimTalk('root.copySelection')

# Вставка
app.ExecuteSimTalk('root.pasteFromClipboard')
```

### Возможности
- ✅ Быстрое создание сложных структур
- ✅ Сохранение соединений
- ✅ Использование готовых шаблонов

### Ограничения
- Требует предварительной подготовки шаблона
- Зависит от буфера обмена Windows

### Статус
⚠️ **Экспериментальный** — для сложных случаев

---

## Стратегия подключения системы

Система **автоматически пробует все методы** в порядке приоритета:

```python
1. COM/DCOM (если доступен)
   ↓
2. REST API (если настроен)
   ↓
3. SimTalk файлы (если PS запущен)
   ↓
4. Демо-режим (если ничего не доступно)
```

### Код определения метода
```python
ps = PlantSimConnection()
connected = ps.check_connection()

if connected:
    print(f"Подключено через: {ps.method.value}")
    # ps.method может быть:
    # - "com"
    # - "rest_api"
    # - "simtalk_file"
    # - "demo"
```

---

## Рекомендации по выбору метода

### Для разработки
✅ **COM/DCOM** — полный контроль, все возможности

### Для интеграции
✅ **REST API** — кроссплатформенность, веб-интерфейс

### Для сложных моделей
✅ **Python Interface** — максимальная гибкость

### Для быстрого прототипирования
✅ **Clipboard** — использование шаблонов

---

## Устранение неполадок

### COM не подключается
```bash
# Проверить процессы
tasklist | findstr PlantSimulation

# Убить zombie-процессы
taskkill /F /IM PlantSimulation.exe
```

### REST API недоступен
```bash
# Проверить порты
netstat -an | findstr 7860

# Проверить настройки PS
# File → Options → REST API → Enable
```

### Python Interface не работает
```python
# Убедиться что используется PS 2404+
# Проверить наличие Python объекта в библиотеке
```

---

## Будущие улучшения

1. **WebSocket** — реальное время для мониторинга
2. **gRPC** — высокопроизводительный RPC
3. **MQTT** — интеграция с IoT
4. **GraphQL** — гибкие запросы к модели

---

## Источники

- [Siemens Plant Simulation Documentation](https://support.sw.siemens.com/)
- [Plant Simulation 2404 Release Notes](https://community.sw.siemens.com/)
- [COM API Reference](https://docs.sw.siemens.com/)
