"""
PS AI Agent — Backend Server (согласно ТЗ)
Автономная система ИИ-агентов для Plant Simulation 2404

Запуск: python backend/main.py
API: http://localhost:7860
"""

import asyncio
import json
import time
import traceback
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

# Добавляем корневую директорию в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from plant_agent_full import Orchestrator, Architect, Builder, Executor, Config

# ─── Global State ─────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.state: str = "idle"
        self.logs: list[dict] = []
        self.log_id: int = 0
        self.spec: Optional[dict] = None
        self.code: str = ""
        self.objects: list[dict] = []
        self.current_task: Optional[asyncio.Task] = None

state = AppState()

# ─── Logging ──────────────────────────────────────────────────────────

def add_log(level: str, agent: str, msg: str):
    state.log_id += 1
    entry = {
        "id": state.log_id,
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "agent": agent,
        "msg": msg,
    }
    state.logs.append(entry)
    if len(state.logs) > 2000:
        state.logs = state.logs[-2000:]
    print(f"[{entry['time']}] [{level}] [{agent}] {msg}")

# ─── API Models ───────────────────────────────────────────────────────

class RunRequest(BaseModel):
    description: str
    output_path: str = "model.spp"

class DryRunRequest(BaseModel):
    description: str

# ─── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    add_log("INFO", "SYSTEM", "PS AI Agent Backend запущен")
    add_log("INFO", "SYSTEM", "API: http://localhost:7860")
    add_log("INFO", "SYSTEM", "Согласно ТЗ v1.0 — Plant Simulation 2404")
    yield
    add_log("INFO", "SYSTEM", "Backend остановлен")

# ─── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(title="PS AI Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Проверка статуса"""
    executor = Executor()
    ps_ok = executor.connect()
    
    ollama_ok = False
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{Config.OLLAMA_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass
    
    return {
        "status": "ok",
        "ollama": ollama_ok,
        "plant_simulation": ps_ok,
    }

@app.get("/logs")
async def get_logs(after: int = 0):
    return [log for log in state.logs if log["id"] > after]

@app.get("/status")
async def get_status():
    return {
        "state": state.state,
        "spec": state.spec,
        "code": state.code,
        "objects": state.objects,
    }

@app.post("/run")
async def run_agent(req: RunRequest):
    """Запустить полный цикл создания модели"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "connecting"
    state.objects = []
    state.spec = None
    state.code = ""
    
    async def task():
        try:
            orchestrator = Orchestrator()
            
            # Шаг 1: Подключение
            add_log("INFO", "SYSTEM", "Подключение к Plant Simulation...")
            state.state = "connecting"
            await asyncio.sleep(0.3)
            
            connected = orchestrator.executor.connect()
            if connected:
                add_log("SUCCESS", "SYSTEM", "Plant Simulation подключен")
            else:
                add_log("WARN", "SYSTEM", "Plant Simulation недоступен — демо-режим")
            
            # Шаг 2: Парсинг
            add_log("INFO", "ARCHITECT", f"Анализ описания: '{req.description[:80]}...'")
            state.state = "parsing"
            await asyncio.sleep(0.3)
            
            spec = orchestrator.architect.parse(req.description)
            state.spec = spec
            add_log("SUCCESS", "ARCHITECT", f"Найдено {len(spec['objects'])} объектов, {len(spec['connections'])} соединений")
            
            # Обновляем объекты для UI
            state.objects = []
            for obj in spec["objects"]:
                state.objects.append({
                    "name": obj["name"],
                    "class": obj["class"],
                    "x": obj.get("x", 0),
                    "y": obj.get("y", 0),
                    "params": obj.get("params", {}),
                })
            
            # Шаг 3: Генерация кода
            add_log("INFO", "BUILDER", "Генерация SimTalk кода...")
            state.state = "building"
            await asyncio.sleep(0.3)
            
            code = orchestrator.builder.generate(spec)
            state.code = code
            add_log("SUCCESS", "BUILDER", f"Сгенерировано {len(code.splitlines())} строк SimTalk")
            
            # Шаг 4: Выполнение
            add_log("INFO", "EXECUTOR", "Выполнение кода в Plant Simulation...")
            state.state = "executing"
            await asyncio.sleep(0.3)
            
            orchestrator.executor.new_model()
            success, error = orchestrator.executor.execute(code)
            
            if success:
                add_log("SUCCESS", "EXECUTOR", "Код выполнен успешно")
            else:
                add_log("ERROR", "EXECUTOR", f"Ошибка: {error}")
                
                # Healing attempts
                for attempt in range(1, Config.MAX_HEALING_ATTEMPTS):
                    add_log("WARN", "DEBUGGER", f"Попытка автоисправления {attempt}/{Config.MAX_HEALING_ATTEMPTS}")
                    await asyncio.sleep(1)
                    orchestrator.executor.new_model()
                    success, error = orchestrator.executor.execute(code)
                    if success:
                        add_log("SUCCESS", "DEBUGGER", "Автоисправление успешно")
                        break
                    else:
                        add_log("ERROR", "DEBUGGER", f"Ошибка: {error}")
            
            # Шаг 5: Валидация
            add_log("INFO", "VALIDATOR", "Валидация модели...")
            valid = orchestrator.validator.validate(spec)
            if valid:
                add_log("SUCCESS", "VALIDATOR", "Валидация пройдена")
            else:
                add_log("ERROR", "VALIDATOR", "Валидация не пройдена")
            
            # Шаг 6: Сохранение
            add_log("INFO", "EXECUTOR", f"Сохранение модели: {req.output_path}")
            saved = orchestrator.executor.save_model(req.output_path)
            if saved:
                add_log("SUCCESS", "EXECUTOR", f"Модель сохранена: {req.output_path}")
            
            state.state = "done"
            add_log("SUCCESS", "SYSTEM", "✅ Задача завершена!")
            
        except Exception as e:
            add_log("ERROR", "SYSTEM", f"Критическая ошибка: {str(e)}")
            add_log("ERROR", "SYSTEM", traceback.format_exc())
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

@app.post("/dry-run")
async def dry_run(req: DryRunRequest):
    """Тестовый запуск без COM"""
    try:
        architect = Architect()
        builder = Builder()
        
        spec = architect.parse(req.description)
        code = builder.generate(spec)
        
        return {
            "spec": spec,
            "code": code,
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/selftest")
async def selftest():
    """Самотестирование"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "testing"
    state.logs = []
    state.log_id = 0
    
    async def task():
        try:
            add_log("INFO", "SYSTEM", "=== САМОТЕСТИРОВАНИЕ ===")
            
            # Тест 1: COM подключение
            add_log("INFO", "TEST", "Тест 1: Подключение к Plant Simulation...")
            executor = Executor()
            connected = executor.connect()
            if connected:
                add_log("SUCCESS", "TEST", "✅ Plant Simulation подключен")
            else:
                add_log("WARN", "TEST", "⚠️ Plant Simulation недоступен (демо-режим)")
            
            await asyncio.sleep(0.3)
            
            # Тест 2: createObject
            add_log("INFO", "TEST", "Тест 2: Проверка createObject...")
            test_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}
var test_obj : object
test_obj := .MaterialFlow.Source.createObject(f, 100, 100)
test_obj.setName("TEST_OBJ")
"""
            success, error = executor.execute(test_code)
            if success:
                add_log("SUCCESS", "TEST", "✅ createObject работает")
            else:
                add_log("ERROR", "TEST", f"❌ createObject: {error}")
            
            await asyncio.sleep(0.3)
            
            # Тест 3: Connector.connect
            add_log("INFO", "TEST", "Тест 3: Проверка Connector.connect...")
            conn_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}
var obj1 : object
obj1 := .MaterialFlow.Source.createObject(f, 200, 100)
obj1.setName("TEST_SRC")
var obj2 : object
obj2 := .MaterialFlow.Station.createObject(f, 320, 100)
obj2.setName("TEST_ST")
.MaterialFlow.Connector.connect(obj1, obj2)
"""
            success, error = executor.execute(conn_code)
            if success:
                add_log("SUCCESS", "TEST", "✅ Connector.connect работает")
            else:
                add_log("ERROR", "TEST", f"❌ Connector.connect: {error}")
            
            await asyncio.sleep(0.3)
            
            # Тест 4: Устаревшие методы
            add_log("INFO", "TEST", "Тест 4: Проверка устаревших методов...")
            old_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}
var old_obj : object
old_obj := .MaterialFlow.SingleProc.createObject(f, 400, 100)
"""
            success, error = executor.execute(old_code)
            if not success:
                add_log("SUCCESS", "TEST", "✅ SingleProc корректно не работает")
            else:
                add_log("WARN", "TEST", "⚠️ SingleProc работает (неожиданно)")
            
            add_log("INFO", "SYSTEM", "=== САМОТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
            state.state = "done"
            
        except Exception as e:
            add_log("ERROR", "TEST", f"Ошибка тестирования: {e}")
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

@app.post("/stop")
async def stop():
    if state.current_task and not state.current_task.done():
        state.current_task.cancel()
        state.state = "idle"
        add_log("WARN", "SYSTEM", "Задача остановлена")
    return {"status": "stopped"}

# ─── Serve Frontend ───────────────────────────────────────────────────

DIST_DIR = Path(__file__).parent.parent / "dist"

if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        file_path = DIST_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")

# ─── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  PS AI Agent — Backend Server (ТЗ v1.0)")
    print("  API: http://localhost:7860")
    print("  Plant Simulation 2404")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=7860)
