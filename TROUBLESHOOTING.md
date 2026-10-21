# Решение проблем при установке PS AI Agent

## Проблема 1: PowerShell блокирует npm

### Ошибка
```
npm : Невозможно загрузить файл C:\Program Files\nodejs\npm.ps1, так как выполнение сценариев отключено в этой системе.
```

### Причина
PowerShell по умолчанию блокирует выполнение скриптов для безопасности.

### Решение

**Способ 1: Через PowerShell (рекомендуется)**
```powershell
# Запустите PowerShell от имени администратора
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Введите Y для подтверждения
```

**Способ 2: Через командную строку (cmd)**
```cmd
# Используйте cmd вместо PowerShell
cmd
cd PS_AI_P
npm install
```

**Способ 3: Временное разрешение**
```powershell
# Разрешите выполнение только для текущей сессии
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
npm install
```

---

## Проблема 2: pywin32==306 не найден

### Ошибка
```
ERROR: Could not find a version that satisfies the requirement pywin32==306
```

### Причина
Версия pywin32==306 устарела, доступна только версия 312+.

### Решение

**Способ 1: Установите последнюю версию**
```powershell
pip install pywin32
```

**Способ 2: Используйте обновленный requirements.txt**
```powershell
cd backend
pip install -r requirements.txt
```

**Способ 3: Укажите диапазон версий**
```powershell
pip install "pywin32>=306"
```

---

## Проблема 3: requirements.txt не найден

### Ошибка
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

### Причина
Вы находитесь не в той папке. Файл requirements.txt находится в папке backend.

### Решение

```powershell
# Перейдите в папку backend
cd backend

# Установите зависимости
pip install -r requirements.txt
```

---

## Проблема 4: pytest не установлен

### Ошибка
```
pytest : Имя "pytest" не распознано как имя командлета
```

### Причина
pytest не установлен в системе.

### Решение

```powershell
pip install pytest
```

---

## Проблема 5: npm install не работает

### Ошибка
```
npm : Невозможно загрузить файл npm.ps1
```

### Решение

**Способ 1: Используйте cmd вместо PowerShell**
```cmd
# Откройте cmd (не PowerShell)
cmd

# Перейдите в папку проекта
cd C:\Windows\system32\PS_AI_P

# Выполните npm install
npm install
```

**Способ 2: Разрешите выполнение скриптов**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
npm install
```

---

## Проблема 6: Plant Simulation не подключается

### Ошибка
```
Plant Simulation не подключен (демо-режим)
```

### Причина
Plant Simulation не запущен или COM интерфейс не зарегистрирован.

### Решение

1. **Запустите Plant Simulation 2404**
   - Откройте Siemens Plant Simulation 2404
   - Дождитесь полной загрузки

2. **Проверьте COM интерфейс**
   ```powershell
   # Проверьте что процесс запущен
   tasklist | findstr PlantSimulation
   ```

3. **Перезапустите Plant Simulation**
   - Закройте Plant Simulation
   - Запустите снова
   - Попробуйте подключиться

4. **Проверьте лицензию**
   - Убедитесь что лицензия активна
   - Проверьте срок действия

---

## Проблема 7: Ollama не отвечает

### Ошибка
```
Ollama недоступна — используется fallback-парсер
```

### Причина
Ollama не запущена или модель не загружена.

### Решение

1. **Запустите Ollama**
   ```powershell
   # Ollama должна работать в фоне
   # Проверьте что процесс запущен
   tasklist | findstr ollama
   ```

2. **Загрузите модель**
   ```powershell
   ollama pull qwen2.5-coder:7b
   ```

3. **Проверьте доступность**
   ```powershell
   curl http://localhost:11434/api/tags
   ```

---

## Проблема 8: Порт 7860 уже используется

### Ошибка
```
Port 7860 already in use
```

### Причина
Другой процесс использует порт 7860.

### Решение

**Способ 1: Найдите и убейте процесс**
```powershell
# Найдите процесс
netstat -ano | findstr :7860

# Убейте процесс (замените PID)
taskkill /F /PID <PID>
```

**Способ 2: Используйте другой порт**
```python
# В файле backend/main.py измените порт:
uvicorn.run(app, host="0.0.0.0", port=8000)  # Вместо 7860
```

---

## Проблема 9: ModuleNotFoundError

### Ошибка
```
ModuleNotFoundError: No module named 'fastapi'
```

### Причина
Python зависимости не установлены.

### Решение

```powershell
cd backend
pip install -r requirements.txt
```

---

## Проблема 10: Frontend не загружается

### Ошибка
Браузер показывает пустую страницу или ошибку 404.

### Причина
Фронтенд не собран или бэкенд не запущен.

### Решение

1. **Соберите фронтенд**
   ```powershell
   npm run build
   ```

2. **Запустите бэкенд**
   ```powershell
   cd backend
   python main.py
   ```

3. **Проверьте что dist папка существует**
   ```powershell
   dir dist
   ```

---

## Диагностика системы

### Проверка всех компонентов

```powershell
# 1. Python
python --version

# 2. Node.js
node --version
npm --version

# 3. Ollama
ollama list

# 4. Plant Simulation
tasklist | findstr PlantSimulation

# 5. Python зависимости
pip list | findstr fastapi
pip list | findstr pywin32

# 6. Порты
netstat -ano | findstr :7860
netstat -ano | findstr :11434
```

### Логи системы

```powershell
# Логи агента
type agent_log.txt

# Логи бэкенда (в консоли PowerShell)
# Смотрите вывод при запуске python main.py
```

---

## Автоматическая диагностика

Создайте файл `diagnose.bat`:

```batch
@echo off
echo ============================================
echo   PS AI Agent — Диагностика
echo ============================================
echo.

echo [1/6] Проверка Python...
python --version
echo.

echo [2/6] Проверка Node.js...
node --version
npm --version
echo.

echo [3/6] Проверка Ollama...
ollama list
echo.

echo [4/6] Проверка Plant Simulation...
tasklist | findstr PlantSimulation
echo.

echo [5/6] Проверка Python зависимостей...
pip list | findstr fastapi
pip list | findstr pywin32
pip list | findstr psutil
echo.

echo [6/6] Проверка портов...
netstat -ano | findstr :7860
netstat -ano | findstr :11434
echo.

echo ============================================
echo   Диагностика завершена
echo ============================================
pause
```

---

## Контакты поддержки

Если проблемы не решены:

1. Проверьте логи в файле `agent_log.txt`
2. Проверьте консоль PowerShell на ошибки
3. Убедитесь что все зависимости установлены
4. Перезапустите систему

**Документация:** README.md, INSTALL_WINDOWS.md, QUICKSTART.md
