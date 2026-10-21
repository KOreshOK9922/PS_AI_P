"""
Оркестратор для Plant Simulation AI Agent
Управляет полным циклом построения модели в PS 2404

Агенты специализированы именно на работе с Plant Simulation:
- Architect: парсит описание линии → JSON-спецификация
- Builder: JSON → SimTalk код (createObject, Connector.connect)
- Executor: выполняет код через COM/REST/Python Interface
- Debugger: анализирует ошибки COM, ищет решения в БЗ
- Researcher: тестирует методы API PS
- Validator: проверяет корректность модели
"""

import asyncio
import time
from typing import Callable, Optional

from parallel_agents import (
    SupervisorAgent,
    ArchitectAgent,
    BuilderAgent,
    ExecutorAgent,
    DebuggerAgent,
    ResearcherAgent,
    ValidatorAgent,
)
from plant_sim import PlantSimConnection
from knowledge_base import kb


class Orchestrator:
    """Оркестратор для Plant Simulation"""
    
    def __init__(
        self,
        description: str,
        output_path: str = "model.spp",
        max_iterations: int = 3,
        log_fn: Optional[Callable] = None,
    ):
        self.description = description
        self.output_path = output_path
        self.max_iterations = max_iterations
        self.log = log_fn or (lambda level, agent, msg: print(f"[{level}] [{agent}] {msg}"))
        
        # Подключение к Plant Simulation
        self.ps = PlantSimConnection()
        
        # Создаём агентов, специализированных на Plant Simulation
        self.supervisor = SupervisorAgent(self.log, self.ps)
        self.architect = ArchitectAgent(self.log)
        self.builder = BuilderAgent(self.log)
        self.executor = ExecutorAgent(self.log, self.ps)
        self.debugger = DebuggerAgent(self.log)
        self.researcher = ResearcherAgent(self.log, self.ps)
        self.validator = ValidatorAgent(self.log, self.ps)
        
        # Состояние
        self.spec = None
        self.code = ""
        self.iteration = 0
    
    async def run(self) -> dict:
        """Запускает полный цикл построения модели в Plant Simulation"""
        start_time = time.time()
        
        try:
            self.log("INFO", "Orchestrator", "🚀 Начало построения модели Plant Simulation")
            
            # Фаза 1: Подключение к PS
            self.log("INFO", "Orchestrator", "🔌 Фаза 1: Подключение к Plant Simulation")
            connected = self.ps.check_connection()
            if connected:
                self.log("SUCCESS", "Orchestrator", f"✅ Подключено через {self.ps.method.value}")
            else:
                self.log("WARN", "Orchestrator", "⚠️ Демо-режим (PS не подключен)")
            
            # Фаза 2: Парсинг описания (Architect)
            self.log("INFO", "Orchestrator", "🏗️ Фаза 2: Архитектор анализирует описание")
            self.architect.status = "working"
            spec_result = await self.architect.execute(self.description)
            
            if not spec_result.success:
                self.log("ERROR", "Orchestrator", f"❌ Архитектор не смог распарсить: {spec_result.error}")
                return {"success": False, "error": "Архитектор не смог распарсить описание"}
            
            self.spec = spec_result.data
            self.architect.status = "done"
            self.log("SUCCESS", "Orchestrator", f"✅ Спецификация: {len(self.spec['objects'])} объектов, {len(self.spec['connections'])} соединений")
            
            # Фаза 3: Генерация SimTalk кода (Builder)
            self.log("INFO", "Orchestrator", "🔨 Фаза 3: Строитель генерирует SimTalk код")
            self.builder.status = "working"
            build_result = await self.builder.execute(self.spec)
            
            if not build_result.success:
                self.log("ERROR", "Orchestrator", f"❌ Строитель не смог сгенерировать код: {build_result.error}")
                return {"success": False, "error": "Строитель не смог сгенерировать код"}
            
            self.code = build_result.data
            self.builder.status = "done"
            self.log("SUCCESS", "Orchestrator", f"✅ Сгенерировано {len(self.code.splitlines())} строк SimTalk")
            
            # Фаза 4: Выполнение кода с циклом отладки
            self.log("INFO", "Orchestrator", "⚡ Фаза 4: Исполнитель выполняет код")
            
            for iteration in range(1, self.max_iterations + 1):
                self.iteration = iteration
                self.log("INFO", "Orchestrator", f"🔄 Итерация {iteration}/{self.max_iterations}")
                
                # Выполнение
                self.executor.status = "working"
                self.ps.new_model()
                exec_result = await self.executor.execute(self.code)
                
                if exec_result.success:
                    self.executor.status = "done"
                    self.log("SUCCESS", "Orchestrator", "✅ Код выполнен успешно")
                    break
                else:
                    self.executor.status = "error"
                    self.log("ERROR", "Orchestrator", f"❌ Ошибка выполнения: {exec_result.error}")
                    
                    # Отладка
                    if iteration < self.max_iterations:
                        self.log("INFO", "Orchestrator", "🐛 Запуск отладчика")
                        self.debugger.status = "working"
                        debug_result = await self.debugger.execute(exec_result.error, self.code)
                        
                        if debug_result.success and isinstance(debug_result.data, str):
                            self.code = debug_result.data
                            self.debugger.status = "done"
                            self.log("SUCCESS", "Orchestrator", "✅ Отладчик предложил исправление")
                        else:
                            self.debugger.status = "error"
                            self.log("WARN", "Orchestrator", "⚠️ Отладчик не смог исправить")
                    else:
                        self.log("ERROR", "Orchestrator", "❌ Превышен лимит итераций")
                        return {
                            "success": False,
                            "error": "Превышен лимит итераций",
                            "spec": self.spec,
                            "code": self.code,
                        }
            
            # Фаза 5: Валидация модели
            self.log("INFO", "Orchestrator", "✅ Фаза 5: Валидатор проверяет модель")
            self.validator.status = "working"
            valid_result = await self.validator.execute(self.spec)
            
            if not valid_result.success:
                self.validator.status = "error"
                self.log("ERROR", "Orchestrator", f"❌ Валидация не пройдена: {valid_result.error}")
                return {
                    "success": False,
                    "error": "Валидация не пройдена",
                    "spec": self.spec,
                    "code": self.code,
                }
            
            self.validator.status = "done"
            self.log("SUCCESS", "Orchestrator", "✅ Модель валидна")
            
            # Фаза 6: Сохранение
            self.log("INFO", "Orchestrator", f"💾 Фаза 6: Сохранение модели в {self.output_path}")
            save_success, save_error = self.ps.save_model(self.output_path)
            
            if save_success:
                self.log("SUCCESS", "Orchestrator", f"✅ Модель сохранена: {self.output_path}")
            else:
                self.log("ERROR", "Orchestrator", f"❌ Ошибка сохранения: {save_error}")
                return {
                    "success": False,
                    "error": f"Ошибка сохранения: {save_error}",
                    "spec": self.spec,
                    "code": self.code,
                }
            
            elapsed = time.time() - start_time
            self.log("SUCCESS", "Orchestrator", f"✨ Модель построена за {elapsed:.1f} сек")
            
            return {
                "success": True,
                "spec": self.spec,
                "code": self.code,
                "iterations": self.iteration,
                "elapsed": elapsed,
            }
            
        except Exception as e:
            self.log("ERROR", "Orchestrator", f"❌ Критическая ошибка: {str(e)}")
            import traceback
            self.log("ERROR", "Orchestrator", traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "spec": self.spec,
                "code": self.code,
            }
    
    async def run_research(self, task: str = "full") -> dict:
        """Запускает исследование API Plant Simulation"""
        self.log("INFO", "Orchestrator", f"🔬 Запуск исследования: {task}")
        
        self.ps.check_connection()
        self.researcher.status = "working"
        result = await self.researcher.execute(task)
        
        if result.success:
            self.researcher.status = "done"
            self.log("SUCCESS", "Orchestrator", "✅ Исследование завершено")
        else:
            self.researcher.status = "error"
            self.log("ERROR", "Orchestrator", f"❌ Ошибка исследования: {result.error}")
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }
