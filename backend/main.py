"""
PS AI Agent — Backend Server v3.0
Оркестратор для автоматизации Plant Simulation 2404

Запуск: python backend/main.py
API: http://localhost:7860
"""

import asyncio
import traceback
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from orchestrator import Orchestrator
from plant_sim import PlantSimConnection
from knowledge_base import kb

# ─── Global State ─────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.state: str = "idle"
        self.logs: list[dict] = []
        self.log_id: int = 0
        self.spec: Optional[dict] = None
        self.code: str = ""
        self.objects: list[dict] = []
        self.agent_statuses: dict = {}
        self.current_task: Optional[asyncio.Task] = None
        self.orchestrator: Optional[Orchestrator] = None

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
    max_iterations: int = 3

class ResearchRequest(BaseModel):
    task: str = "full"

# ─── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    add_log("INFO", "SYSTEM", "PS AI Agent Backend v3.0 запущен")
    add_log("INFO", "SYSTEM", "Оркестратор для Plant Simulation 2404")
    add_log("INFO", "SYSTEM", "API: http://localhost:7860")
    yield
    add_log("INFO", "SYSTEM", "Backend остановлен")

# ─── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(title="PS AI Agent v3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Endpoints ────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Корневой маршрут"""
    dist_dir = Path(__file__).parent.parent / "dist"
    index_file = dist_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>PS AI Agent - Backend Running</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #030712; color: #e5e7eb; }
                    h1 { color: #3b82f6; }
                    .success { color: #10b981; }
                    .warning { color: #f59e0b; }
                    code { background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 4px; }
                    pre { background: #1f2937; color: #e5e7eb; padding: 15px; border-radius: 8px; overflow-x: auto; }
                    a { color: #3b82f6; }
                </style>
            </head>
            <body>
                <h1>🏭 PS AI Agent Backend</h1>
                <p class="success">✅ Backend работает успешно!</p>
                
                <h2>📚 API Документация</h2>
                <ul>
                    <li><a href="/docs">Swagger UI</a> - интерактивная документация API</li>
                    <li><a href="/redoc">ReDoc</a> - альтернативная документация</li>
                    <li><a href="/health">Health Check</a> - проверка статуса</li>
                </ul>
                
                <h2>⚠️ Frontend не собран</h2>
                <p>Для работы веб-интерфейса выполните:</p>
                <pre>npm run build</pre>
            </body>
            </html>
            """,
            status_code=200
        )

@app.get("/health")
async def health():
    """Проверка статуса"""
    ps = PlantSimConnection()
    ps_ok = ps.check_connection()
    conn_info = ps.get_connection_info()
    
    return {
        "status": "ok",
        "plant_simulation": ps_ok,
        "connection_method": conn_info["method"],
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
        "agents": state.agent_statuses,
    }

@app.get("/agents")
async def get_agents():
    """Статус всех агентов"""
    return state.agent_statuses

@app.get("/knowledge")
async def get_knowledge():
    """База знаний"""
    return kb.export_knowledge()

@app.get("/knowledge/methods")
async def get_methods():
    """Все методы API с статистикой"""
    return kb.get_all_methods()

@app.get("/knowledge/classes")
async def get_classes():
    """Все известные классы"""
    return kb.get_all_classes()

@app.post("/run")
async def run_agent(req: RunRequest):
    """Запустить построение модели в Plant Simulation"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "initializing"
    state.objects = []
    state.spec = None
    state.code = ""
    state.agent_statuses = {}
    
    async def task():
        try:
            add_log("INFO", "SYSTEM", "Инициализация оркестратора...")
            state.state = "connecting"
            
            # Создаём оркестратор
            orchestrator = Orchestrator(
                description=req.description,
                output_path=req.output_path,
                max_iterations=req.max_iterations,
                log_fn=add_log
            )
            state.orchestrator = orchestrator
            
            # Запускаем построение модели
            state.state = "running"
            result = await orchestrator.run()
            
            # Обновляем состояние
            if result.get("spec"):
                state.spec = result["spec"]
                state.objects = [
                    {
                        "name": obj["name"],
                        "class": obj["class"],
                        "x": obj.get("x", 0),
                        "y": obj.get("y", 0),
                        "params": obj.get("params", {}),
                    }
                    for obj in result["spec"].get("objects", [])
                ]
            
            if result.get("code"):
                state.code = result["code"]
            
            # Обновляем статусы агентов
            state.agent_statuses = {
                "Architect": orchestrator.architect.status,
                "Builder": orchestrator.builder.status,
                "Executor": orchestrator.executor.status,
                "Debugger": orchestrator.debugger.status,
                "Validator": orchestrator.validator.status,
            }
            
            if result.get("success"):
                state.state = "done"
                add_log("SUCCESS", "SYSTEM", f"✅ Модель построена за {result.get('elapsed', 0):.1f} сек")
            else:
                state.state = "error"
                add_log("ERROR", "SYSTEM", f"❌ Ошибка: {result.get('error')}")
            
        except Exception as e:
            add_log("ERROR", "SYSTEM", f"Критическая ошибка: {str(e)}")
            add_log("ERROR", "SYSTEM", traceback.format_exc())
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

@app.post("/research")
async def run_research(req: ResearchRequest):
    """Запустить исследование API Plant Simulation"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "researching"
    
    async def task():
        try:
            orchestrator = Orchestrator(
                description="",
                log_fn=add_log
            )
            state.orchestrator = orchestrator
            
            add_log("INFO", "SYSTEM", f"Запуск исследования: {req.task}")
            result = await orchestrator.run_research(req.task)
            
            if result.get("success"):
                state.state = "done"
                add_log("SUCCESS", "SYSTEM", "✅ Исследование завершено")
            else:
                state.state = "error"
                add_log("ERROR", "SYSTEM", f"❌ Ошибка: {result.get('error')}")
            
        except Exception as e:
            add_log("ERROR", "SYSTEM", f"Ошибка: {e}")
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

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
            
            ps = PlantSimConnection()
            connected = ps.check_connection()
            
            if connected:
                add_log("SUCCESS", "TEST", f"✅ Подключено через {ps.method.value}")
            else:
                add_log("WARN", "TEST", "⚠️ Демо-режим")
            
            await asyncio.sleep(0.3)
            
            # Тест createObject
            add_log("INFO", "TEST", "Тест: createObject")
            test_code = """
var f : object
f := .Models.Model
var obj : object
obj := .MaterialFlow.Source.createObject(f, 100, 100)
obj.setName("TEST")
"""
            success, error = ps.execute(test_code)
            if success:
                add_log("SUCCESS", "TEST", "✅ createObject работает")
            else:
                add_log("ERROR", "TEST", f"❌ {error}")
            
            await asyncio.sleep(0.3)
            
            # Тест Connector.connect
            add_log("INFO", "TEST", "Тест: Connector.connect")
            conn_code = """
var f : object
f := .Models.Model
var obj1 : object
obj1 := .MaterialFlow.Source.createObject(f, 200, 100)
obj1.setName("SRC")
var obj2 : object
obj2 := .MaterialFlow.Station.createObject(f, 320, 100)
obj2.setName("ST")
.MaterialFlow.Connector.connect(obj1, obj2)
"""
            success, error = ps.execute(conn_code)
            if success:
                add_log("SUCCESS", "TEST", "✅ Connector.connect работает")
            else:
                add_log("ERROR", "TEST", f"❌ {error}")
            
            add_log("INFO", "SYSTEM", "=== САМОТЕСТИРОВАНИЕ ЗАВЕРШЕНО ===")
            state.state = "done"
            
        except Exception as e:
            add_log("ERROR", "TEST", f"Ошибка: {e}")
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

if DIST_DIR.exists() and (DIST_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        if path.startswith("api/") or path in ["docs", "redoc", "openapi.json"]:
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = DIST_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")

# ─── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  PS AI Agent v3.0 — Backend Server")
    print("  Оркестратор для Plant Simulation 2404")
    print("  API: http://localhost:7860")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=7860)
