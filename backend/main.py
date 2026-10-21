"""
Мультиагентная система генерации кода
Главный сервер
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from orchestrator import Orchestrator
from llm_client import OllamaClient

# ─── Models ───────────────────────────────────────────────────────────

class TaskRequest(BaseModel):
    requirement: str
    max_iterations: int = 3
    timeout: int = 600  # 10 минут

class TaskStatus(BaseModel):
    task_id: str
    status: str
    phase: str
    agents: dict
    logs: list
    artifacts: dict

# ─── Global State ─────────────────────────────────────────────────────

tasks = {}
logs = {}

# ─── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(title="Multi-Agent Code Generation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Helper Functions ─────────────────────────────────────────────────

def add_log(task_id: str, agent: str, message: str, level: str = "INFO"):
    if task_id not in logs:
        logs[task_id] = []
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "agent": agent,
        "message": message,
        "level": level
    }
    logs[task_id].append(log_entry)
    print(f"[{log_entry['timestamp']}] [{agent}] {message}")

# ─── Endpoints ────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "service": "Multi-Agent Code Generation System"}

@app.get("/health")
async def health():
    client = OllamaClient()
    ollama_ok = await client.check_health()
    return {
        "status": "ok",
        "ollama": ollama_ok,
        "active_tasks": len([t for t in tasks.values() if t["status"] == "running"])
    }

@app.post("/api/run")
async def run_task(request: TaskRequest):
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = {
        "task_id": task_id,
        "requirement": request.requirement,
        "status": "running",
        "phase": "initialization",
        "agents": {},
        "artifacts": {},
        "max_iterations": request.max_iterations,
        "created_at": datetime.now().isoformat()
    }
    
    logs[task_id] = []
    
    # Запускаем задачу в фоне
    asyncio.create_task(execute_task(task_id, request))
    
    return {"task_id": task_id, "status": "started"}

async def execute_task(task_id: str, request: TaskRequest):
    """Выполняет задачу мультиагентной системой"""
    try:
        add_log(task_id, "Orchestrator", "Запуск мультиагентной системы")
        
        # Создаём оркестратор
        orchestrator = Orchestrator(
            task_id=task_id,
            requirement=request.requirement,
            max_iterations=request.max_iterations,
            log_fn=lambda agent, msg, level="INFO": add_log(task_id, agent, msg, level)
        )
        
        # Обновляем статус
        tasks[task_id]["phase"] = "analysis"
        
        # Выполняем workflow
        result = await orchestrator.run()
        
        # Сохраняем артефакты
        tasks[task_id]["artifacts"] = result.get("artifacts", {})
        tasks[task_id]["status"] = "completed" if result.get("success") else "failed"
        tasks[task_id]["phase"] = "completed"
        
        add_log(task_id, "Orchestrator", 
                f"Задача завершена: {'успешно' if result.get('success') else 'с ошибками'}")
        
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["phase"] = "error"
        add_log(task_id, "Orchestrator", f"Критическая ошибка: {str(e)}", "ERROR")

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": tasks[task_id]["status"],
        "phase": tasks[task_id]["phase"],
        "agents": tasks[task_id]["agents"],
        "artifacts": tasks[task_id]["artifacts"],
        "created_at": tasks[task_id]["created_at"]
    }

@app.get("/api/logs/{task_id}")
async def get_logs(task_id: str, after: int = 0):
    if task_id not in logs:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return logs[task_id][after:]

@app.get("/api/artifacts/{task_id}")
async def get_artifacts(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id].get("artifacts", {})

@app.get("/api/tasks")
async def list_tasks():
    return [
        {
            "task_id": tid,
            "status": t["status"],
            "phase": t["phase"],
            "created_at": t["created_at"],
            "requirement": t["requirement"][:100] + "..." if len(t["requirement"]) > 100 else t["requirement"]
        }
        for tid, t in tasks.items()
    ]

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
    
    print("=" * 70)
    print("  Multi-Agent Code Generation System")
    print("  API: http://localhost:8000")
    print("  7 специализированных агентов")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
