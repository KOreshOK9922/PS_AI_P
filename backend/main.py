"""
PS AI Agent — Backend Server
Автономная система ИИ-агентов для Plant Simulation 2404

Запуск: python backend/main.py
API: http://localhost:8000
"""

import asyncio
import json
import time
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents import AgentSwarm
from researcher import APIResearcher
from plant_sim import PlantSimConnection
from ollama_client import OllamaClient

# ─── Global State ─────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.state: str = "idle"
        self.logs: list[dict] = []
        self.log_id: int = 0
        self.objects: list[dict] = []
        self.research: list[dict] = []
        self.current_task: Optional[asyncio.Task] = None
        self.swarm: Optional[AgentSwarm] = None
        self.researcher: Optional[APIResearcher] = None

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
    # Keep last 1000 logs
    if len(state.logs) > 1000:
        state.logs = state.logs[-1000:]
    print(f"[{entry['time']}] [{level}] [{agent}] {msg}")

# ─── API Models ───────────────────────────────────────────────────────

class RunRequest(BaseModel):
    description: str
    auto_research: bool = True

# ─── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    add_log("INFO", "SYSTEM", "PS AI Agent Backend запущен")
    add_log("INFO", "SYSTEM", f"API: http://localhost:8000")
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
    """Проверка статуса всех систем"""
    ollama_ok = False
    ps_ok = False
    
    try:
        client = OllamaClient()
        ollama_ok = await client.check_health()
    except Exception:
        pass
    
    try:
        conn = PlantSimConnection()
        ps_ok = conn.check_connection()
    except Exception:
        pass
    
    return {
        "status": "ok",
        "ollama": ollama_ok,
        "plant_simulation": ps_ok,
    }

@app.get("/logs")
async def get_logs(after: int = 0):
    """Получить логи после указанного ID"""
    return [log for log in state.logs if log["id"] > after]

@app.get("/status")
async def get_status():
    """Получить текущий статус системы"""
    return {
        "state": state.state,
        "objects": state.objects,
        "research": state.research,
    }

@app.post("/run")
async def run_agent(req: RunRequest):
    """Запустить агента для построения модели"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "connecting"
    state.objects = []
    
    async def task():
        try:
            swarm = AgentSwarm(add_log)
            state.swarm = swarm
            
            # Phase 1: Подключение
            add_log("INFO", "SYSTEM", "Подключение к Ollama...")
            state.state = "connecting"
            ollama = OllamaClient()
            if not await ollama.check_health():
                add_log("WARN", "SYSTEM", "Ollama недоступна — используется fallback-парсер")
            
            add_log("INFO", "SYSTEM", "Подключение к Plant Simulation...")
            ps = PlantSimConnection()
            if not ps.check_connection():
                add_log("WARN", "SYSTEM", "Plant Simulation не запущен — демо-режим")
            
            # Phase 2: Парсинг описания
            add_log("INFO", "ARCHITECT", f"Анализ описания: '{req.description[:80]}...'")
            state.state = "parsing"
            await asyncio.sleep(0.5)
            
            specification = await swarm.architect.parse(req.description, ollama)
            add_log("SUCCESS", "ARCHITECT", f"Найдено {len(specification['objects'])} объектов, {len(specification['connections'])} соединений")
            
            # Phase 3: Генерация кода
            add_log("INFO", "BUILDER", "Генерация SimTalk кода...")
            state.state = "building"
            await asyncio.sleep(0.3)
            
            code_blocks = swarm.builder.generate(specification)
            add_log("SUCCESS", "BUILDER", f"Сгенерировано {len(code_blocks)} блоков кода")
            
            # Phase 4: Выполнение
            add_log("INFO", "EXECUTOR", "Создание модели в Plant Simulation...")
            state.state = "executing"
            
            results = await swarm.executor.execute(code_blocks, ps)
            
            # Обновляем объекты
            state.objects = []
            for obj in specification["objects"]:
                state.objects.append({
                    "name": obj["name"],
                    "class": obj["class"],
                    "params": obj.get("params", {}),
                    "x": 0,
                    "y": 0,
                    "connected": False,
                })
            
            # Проверяем соединения
            connection_results = results.get("connections", [])
            for i, conn_result in enumerate(connection_results):
                if i < len(state.objects) - 1:
                    state.objects[i]["connected"] = conn_result.get("success", False)
            
            if results.get("all_connected"):
                add_log("SUCCESS", "EXECUTOR", "Все соединения созданы!")
            else:
                failed = [r for r in connection_results if not r.get("success")]
                if failed and req.auto_research:
                    add_log("WARN", "EXECUTOR", f"{len(failed)} соединений не создано")
                    add_log("INFO", "RESEARCHER", "Запуск авто-исследования методов соединений...")
                    state.state = "researching"
                    
                    researcher = APIResearcher(add_log, ps)
                    state.researcher = researcher
                    found = await researcher.find_connection_method()
                    state.research = researcher.results
                    
                    if found:
                        add_log("SUCCESS", "RESEARCHER", f"Найден рабочий метод: {found['method']}")
                        # Пробуем применить найденный метод
                        retry_results = await swarm.executor.retry_connections(found, ps)
                        for i, r in enumerate(retry_results):
                            if r.get("success") and i < len(state.objects) - 1:
                                state.objects[i]["connected"] = True
                    else:
                        add_log("WARN", "RESEARCHER", "Рабочий метод соединений не найден")
            
            # Phase 5: Сохранение
            add_log("INFO", "EXECUTOR", "Сохранение модели...")
            saved = await swarm.validator.save(ps)
            if saved:
                add_log("SUCCESS", "EXECUTOR", "Модель сохранена!")
            
            state.state = "done"
            add_log("SUCCESS", "SYSTEM", "Задача завершена!")
            
        except Exception as e:
            add_log("ERROR", "SYSTEM", f"Ошибка: {str(e)}")
            add_log("ERROR", "SYSTEM", traceback.format_exc())
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

@app.post("/research")
async def run_research():
    """Запустить авто-исследование API"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "researching"
    state.research = []
    
    async def task():
        try:
            add_log("INFO", "RESEARCHER", "Запуск авто-исследования API Plant Simulation")
            
            ps = PlantSimConnection()
            researcher = APIResearcher(add_log, ps)
            state.researcher = researcher
            
            await researcher.full_research()
            state.research = researcher.results
            
            state.state = "done"
            add_log("SUCCESS", "RESEARCHER", f"Исследование завершено. Проверено {len(researcher.results)} методов.")
            
        except Exception as e:
            add_log("ERROR", "RESEARCHER", f"Ошибка исследования: {str(e)}")
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

@app.post("/stop")
async def stop():
    """Остановить текущую задачу"""
    if state.current_task and not state.current_task.done():
        state.current_task.cancel()
        state.state = "idle"
        add_log("WARN", "SYSTEM", "Задача остановлена пользователем")
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
    print("  PS AI Agent — Backend Server")
    print("  API: http://localhost:8000")
    print("  Frontend: http://localhost:8000 (после npm run build)")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
