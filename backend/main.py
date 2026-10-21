"""
PS AI Agent — Backend Server v2.0
С параллельными агентами и базой знаний

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

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from plant_sim import PlantSimConnection
from parallel_agents import SupervisorAgent, AgentStatus
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
        self.ps: Optional[PlantSimConnection] = None
        self.supervisor: Optional[SupervisorAgent] = None

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
    parallel_research: bool = False

class ResearchRequest(BaseModel):
    task: str = "full"

# ─── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    add_log("INFO", "SYSTEM", "PS AI Agent Backend v2.0 запущен")
    add_log("INFO", "SYSTEM", "Параллельные агенты + база знаний")
    add_log("INFO", "SYSTEM", "API: http://localhost:7860")
    yield
    add_log("INFO", "SYSTEM", "Backend остановлен")

# ─── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(title="PS AI Agent v2.0", lifespan=lifespan)

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
    """Корневой маршрут - отдаёт frontend"""
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
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    h1 { color: #3b82f6; }
                    .success { color: #10b981; }
                    .warning { color: #f59e0b; }
                    code { background: #1f2937; color: #10b981; padding: 2px 6px; border-radius: 4px; }
                    pre { background: #1f2937; color: #e5e7eb; padding: 15px; border-radius: 8px; overflow-x: auto; }
                </style>
            </head>
            <body>
                <h1>🏭 PS AI Agent Backend</h1>
                <p class="success">✅ Backend работает успешно!</p>
                
                <h2>⚠️ Frontend не собран</h2>
                <p>Для работы веб-интерфейса выполните:</p>
                <pre>npm run build</pre>
                
                <h2>📚 API Документация</h2>
                <ul>
                    <li><a href="/docs">Swagger UI</a> - интерактивная документация API</li>
                    <li><a href="/redoc">ReDoc</a> - альтернативная документация</li>
                    <li><a href="/health">Health Check</a> - проверка статуса</li>
                </ul>
                
                <h2>🚀 Быстрый старт</h2>
                <pre>
# 1. Соберите frontend
npm run build

# 2. Перезапустите backend
python backend/main.py

# 3. Откройте браузер
http://localhost:7860
                </pre>
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
    """Запустить полный цикл с параллельными агентами"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "initializing"
    state.objects = []
    state.spec = None
    state.code = ""
    state.agent_statuses = {}
    
    async def task():
        try:
            # Инициализация
            add_log("INFO", "SYSTEM", "Инициализация системы...")
            state.state = "connecting"
            
            ps = PlantSimConnection()
            state.ps = ps
            connected = ps.check_connection()
            
            if connected:
                add_log("SUCCESS", "SYSTEM", f"Plant Simulation подключен ({ps.method.value})")
            else:
                add_log("WARN", "SYSTEM", "Plant Simulation в демо-режиме")
            
            # Создаём супервизора
            supervisor = SupervisorAgent(add_log, ps)
            state.supervisor = supervisor
            
            # Если запрошено параллельное исследование
            if req.parallel_research:
                add_log("INFO", "SYSTEM", "Запуск параллельного исследования...")
                state.state = "researching"
                research_result = await supervisor.run_parallel_research()
                add_log("SUCCESS", "SYSTEM", f"Исследование завершено")
            
            # Запускаем основной конвейер
            state.state = "parsing"
            add_log("INFO", "Supervisor", "Запуск конвейера обработки")
            
            result = await supervisor.run_pipeline(req.description)
            
            # Обновляем статусы агентов
            state.agent_statuses = {
                "Architect": supervisor.architect.status.value,
                "Builder": supervisor.builder.status.value,
                "Executor": supervisor.executor.status.value,
                "Debugger": supervisor.debugger.status.value,
                "Validator": supervisor.validator.status.value,
            }
            
            if result["success"]:
                state.spec = result.get("spec")
                state.code = result.get("code")
                
                # Обновляем объекты для UI
                if state.spec:
                    state.objects = []
                    for obj in state.spec["objects"]:
                        state.objects.append({
                            "name": obj["name"],
                            "class": obj["class"],
                            "x": obj.get("x", 0),
                            "y": obj.get("y", 0),
                            "params": obj.get("params", {}),
                        })
                
                # Сохраняем модель
                add_log("INFO", "SYSTEM", f"Сохранение модели: {req.output_path}")
                ps.save_model(req.output_path)
                
                state.state = "done"
                add_log("SUCCESS", "SYSTEM", "✅ Модель создана и сохранена!")
            else:
                state.state = "error"
                add_log("ERROR", "SYSTEM", f"Ошибка: {result.get('error')}")
            
        except Exception as e:
            add_log("ERROR", "SYSTEM", f"Критическая ошибка: {str(e)}")
            add_log("ERROR", "SYSTEM", traceback.format_exc())
            state.state = "error"
    
    state.current_task = asyncio.create_task(task())
    return {"status": "started"}

@app.post("/research")
async def run_research(req: ResearchRequest):
    """Запустить исследование API"""
    if state.current_task and not state.current_task.done():
        return {"error": "Уже выполняется задача"}
    
    state.state = "researching"
    
    async def task():
        try:
            ps = PlantSimConnection()
            ps.check_connection()
            
            supervisor = SupervisorAgent(add_log, ps)
            state.supervisor = supervisor
            
            add_log("INFO", "Researcher", f"Запуск исследования: {req.task}")
            
            from parallel_agents import ResearcherAgent
            researcher = ResearcherAgent(add_log, ps)
            
            result = await researcher.execute(req.task)
            
            if result.success:
                add_log("SUCCESS", "Researcher", "Исследование завершено")
                state.state = "done"
            else:
                add_log("ERROR", "Researcher", f"Ошибка: {result.error}")
                state.state = "error"
            
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
        # Не перехватываем API маршруты
        if path.startswith("api/") or path in ["docs", "redoc", "openapi.json", "health", "logs", "status", "agents", "knowledge"]:
            raise HTTPException(status_code=404, detail="Not found")
        
        file_path = DIST_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")

# ─── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  PS AI Agent v2.0 — Backend Server")
    print("  Параллельные агенты + база знаний")
    print("  API: http://localhost:7860")
    print("  Plant Simulation 2404")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=7860)
