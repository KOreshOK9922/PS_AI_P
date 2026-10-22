# 🚨 СРОЧНО: Исправление критических проблем

## ⚠️ КРИТИЧЕСКАЯ ПРОБЛЕМА: Проект в system32!

Ваш проект находится в `C:\Windows\system32\PS_AI_P\` — это **системная директория Windows**!
Это может привести к:
- Повреждению системных файлов
- Проблемам с правами доступа
- Невозможности нормальной работы

## ✅ РЕШЕНИЕ: Переместить проект в безопасное место

### Шаг 1: Остановите все процессы

Закройте все терминалы PowerShell, где запущен backend.

### Шаг 2: Переместите проект

Откройте PowerShell **от имени администратора** и выполните:

```powershell
# Создайте директорию для проектов
New-Item -ItemType Directory -Path "C:\Projects" -Force

# Переместите проект
Move-Item -Path "C:\Windows\system32\PS_AI_P" -Destination "C:\Projects\PS_AI_P" -Force

# Перейдите в новую директорию
cd C:\Projects\PS_AI_P
```

### Шаг 3: Проверьте структуру

```powershell
# Должны увидеть:
dir

# backend/
# src/
# package.json
# README.md
# ...
```

### Шаг 4: Удалите старые зависимости

```powershell
# Удалите node_modules и package-lock.json
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue

# Удалите venv если есть
Remove-Item -Recurse -Force backend\venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\node_modules -ErrorAction SilentlyContinue
```

### Шаг 5: Создайте виртуальное окружение

```powershell
cd backend

# Создайте venv
python -m venv venv

# Активируйте venv (правильный синтаксис для PowerShell!)
.\venv\Scripts\Activate.ps1

# Если не работает, попробуйте:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
```

### Шаг 6: Установите зависимости

```powershell
# Обновите pip
python -m pip install --upgrade pip

# Установите Python зависимости
pip install -r requirements.txt

# Вернитесь в корень и установите Node.js зависимости
cd ..
npm install
```

### Шаг 7: Соберите frontend

```powershell
npm run build
```

### Шаг 8: Запустите backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

Откройте: **http://localhost:7860**

---

## 🐛 Если возникают ошибки

### Ошибка: "pywin32==306 not found"

**Решение:** requirements.txt уже исправлен, использует `pywin32>=306`

### Ошибка: "npm.ps1 cannot be loaded"

**Решение:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Ошибка: "venv\Scripts\Activate.ps1 не работает"

**Решение:**
```powershell
# Используйте cmd вместо PowerShell
cmd
cd backend
venv\Scripts\activate
```

### Ошибка: "404 Not Found" на http://localhost:7860

**Решение:** Backend теперь имеет корневой маршрут. Если видите HTML страницу с инструкциями — значит frontend не собран. Выполните:
```powershell
npm run build
```

---

## 📁 Правильная структура проекта

```
C:\Projects\PS_AI_P\
├── backend/
│   ├── venv/              ← Виртуальное окружение
│   ├── main.py            ← Backend сервер
│   ├── plant_sim.py
│   ├── parallel_agents.py
│   ├── knowledge_base.py
│   └── requirements.txt   ← Исправлен (>= вместо ==)
├── src/
│   └── App.tsx            ← Frontend
├── dist/                  ← Собранный frontend (после npm run build)
├── node_modules/
├── package.json
├── index.html
└── README.md
```

---

## ✅ Чек-лист проверки

- [ ] Проект перемещён из `C:\Windows\system32\` в `C:\Projects\`
- [ ] Создано виртуальное окружение `backend\venv`
- [ ] Venv активирован (видно `(venv)` в начале строки PowerShell)
- [ ] Python зависимости установлены (`pip install -r requirements.txt`)
- [ ] Node.js зависимости установлены (`npm install`)
- [ ] Frontend собран (`npm run build`)
- [ ] Backend запущен (`python backend\main.py`)
- [ ] Открывается http://localhost:7860

---

## 🎯 Быстрый старт после исправлений

```powershell
# 1. Перейти в проект
cd C:\Projects\PS_AI_P

# 2. Активировать venv
cd backend
.\venv\Scripts\Activate.ps1

# 3. Запустить backend
python main.py

# 4. Открыть браузер
# http://localhost:7860
```

---

## 📞 Если ничего не помогает

1. Проверьте логи в консоли PowerShell
2. Проверьте файл `agent_log.txt`
3. Убедитесь что порт 7860 не занят:
   ```powershell
   netstat -ano | findstr :7860
   ```
4. Перезапустите компьютер и попробуйте снова

---

**После выполнения всех шагов проект будет работать корректно!** ✅
