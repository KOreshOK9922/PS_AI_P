# 🚀 Быстрый старт для Windows

## Установка (один раз)

### Способ 1: Автоматическая установка (рекомендуется)

1. **Двойной клик** на файл `install_windows.bat`
2. Дождитесь завершения установки
3. Готово!

### Способ 2: Ручная установка

Откройте PowerShell и выполните:

```powershell
# 1. Разрешите выполнение скриптов
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 2. Установите Python зависимости
cd backend
pip install -r requirements.txt

# 3. Установите Node.js зависимости
cd ..
npm install

# 4. Соберите фронтенд
npm run build
```

---

## Подготовка (один раз)

### 1. Установите Ollama

```powershell
# Скачайте с https://ollama.com/download
# Установите и загрузите модель:
ollama pull qwen2.5-coder:7b
```

### 2. Запустите Plant Simulation 2404

Откройте Siemens Plant Simulation 2404

---

## Запуск системы

### Способ 1: Через batch файл (просто)

**Двойной клик** на файл `start_server.bat`

### Способ 2: Через PowerShell

```powershell
cd backend
python main.py
```

---

## Использование

1. Откройте браузер: **http://localhost:7860**
2. Введите описание линии, например:
   ```
   Линия: источник заготовок с интервалом 3 минуты, 
   станция обработки 20 секунд, накопитель на 10 мест, сход
   ```
3. Нажмите **"▶ Запустить"**
4. Наблюдайте за работой агентов!

---

## Решение проблем

### Ошибка: `pywin32==306 not found`

```powershell
pip install pywin32
```

### Ошибка: `npm.ps1 cannot be loaded`

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Ошибка: `requirements.txt not found`

```powershell
cd backend
pip install -r requirements.txt
```

### Ошибка: `Plant Simulation не подключается`

1. Убедитесь что Plant Simulation 2404 запущен
2. Проверьте что COM интерфейс зарегистрирован
3. Перезапустите Plant Simulation

---

## Структура файлов

```
PS_AI_P/
├── install_windows.bat    ← Запустите для установки
├── start_server.bat       ← Запустите для запуска системы
├── backend/
│   ├── main.py
│   └── requirements.txt
└── ...
```

---

## Проверка установки

```powershell
# Проверьте Python
python --version

# Проверьте Node.js
node --version

# Проверьте Ollama
ollama list

# Проверьте Plant Simulation
tasklist | findstr PlantSimulation
```

---

## Готово! 🎉

Теперь вы можете:
- ✅ Создавать модели автоматически
- ✅ Использовать параллельных агентов
- ✅ Накопить базу знаний
- ✅ Исследовать API Plant Simulation

**Документация:** README.md, INSTALL_WINDOWS.md
