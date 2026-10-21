"""
Оркестратор - управляет жизненным циклом задачи
"""

import asyncio
from typing import Callable, Optional

from agents.analyst import ProductAnalyst
from agents.architect import SystemArchitect
from agents.engineer import LeadEngineer
from agents.qa import QAEngineer
from agents.reviewer import CodeReviewer
from agents.devops import DevOpsEngineer
from llm_client import OllamaClient


class Orchestrator:
    """Оркестратор мультиагентной системы"""
    
    def __init__(
        self,
        task_id: str,
        requirement: str,
        max_iterations: int = 3,
        log_fn: Optional[Callable] = None
    ):
        self.task_id = task_id
        self.requirement = requirement
        self.max_iterations = max_iterations
        self.log = log_fn or (lambda agent, msg, level="INFO": print(f"[{agent}] {msg}"))
        
        # Инициализируем LLM клиент
        self.llm = OllamaClient()
        
        # Инициализируем агентов
        self.analyst = ProductAnalyst(self.llm, self.log)
        self.architect = SystemArchitect(self.llm, self.log)
        self.engineer = LeadEngineer(self.llm, self.log)
        self.qa = QAEngineer(self.llm, self.log)
        self.reviewer = CodeReviewer(self.llm, self.log)
        self.devops = DevOpsEngineer(self.llm, self.log)
        
        # Состояние задачи
        self.artifacts = {}
        self.current_iteration = 0
    
    async def run(self) -> dict:
        """Запускает полный workflow"""
        try:
            self.log("Orchestrator", "🚀 Начало выполнения задачи")
            
            # Фаза 1: Анализ требований
            self.log("Orchestrator", "📊 Фаза 1: Анализ требований")
            requirements = await self.analyst.analyze(self.requirement)
            self.artifacts["requirements.md"] = requirements
            self.log("Product Analyst", "✅ Требования сформированы")
            
            # Фаза 2: Проектирование архитектуры
            self.log("Orchestrator", "🏛️ Фаза 2: Проектирование архитектуры")
            architecture = await self.architect.design(requirements)
            self.artifacts["architecture.md"] = architecture
            self.log("System Architect", "✅ Архитектура спроектирована")
            
            # Фаза 3-6: Цикл реализации и проверки
            code = None
            tests = None
            review_report = None
            
            for iteration in range(1, self.max_iterations + 1):
                self.current_iteration = iteration
                self.log("Orchestrator", f"🔄 Итерация {iteration}/{self.max_iterations}")
                
                # Фаза 3: Реализация кода
                self.log("Orchestrator", "💻 Фаза 3: Реализация кода")
                code = await self.engineer.implement(requirements, architecture, review_report)
                self.artifacts["code"] = code
                self.log("Lead Engineer", "✅ Код реализован")
                
                # Фаза 4: Тестирование
                self.log("Orchestrator", "🧪 Фаза 4: Тестирование")
                tests = await self.qa.test(code, requirements)
                self.artifacts["tests"] = tests
                
                if tests.get("passed", False):
                    self.log("QA Engineer", "✅ Все тесты пройдены")
                else:
                    self.log("QA Engineer", f"❌ Тесты не пройдены: {tests.get('failures', [])}", "WARN")
                    review_report = {"type": "qa_failures", "issues": tests.get("failures", [])}
                    continue
                
                # Фаза 5: Ревью кода
                self.log("Orchestrator", "🔍 Фаза 5: Ревью кода")
                review = await self.reviewer.review(code, architecture)
                self.artifacts["review.md"] = review
                
                if review.get("approved", False):
                    self.log("Code Reviewer", "✅ Код одобрен")
                    break
                else:
                    self.log("Code Reviewer", f"❌ Код не одобрен: {review.get('issues', [])}", "WARN")
                    review_report = review
                    continue
            
            # Проверка на превышение лимита итераций
            if not tests.get("passed", False) or not review.get("approved", False):
                self.log("Orchestrator", "⚠️ Превышен лимит итераций", "WARN")
                return {
                    "success": False,
                    "artifacts": self.artifacts,
                    "error": "Превышен лимит итераций"
                }
            
            # Фаза 6: Упаковка
            self.log("Orchestrator", "🚀 Фаза 6: Упаковка")
            docker_config = await self.devops.package(code, requirements, architecture)
            self.artifacts["Dockerfile"] = docker_config.get("Dockerfile", "")
            self.artifacts["docker-compose.yml"] = docker_config.get("docker-compose.yml", "")
            self.artifacts["ci.yml"] = docker_config.get("ci.yml", "")
            self.log("DevOps Engineer", "✅ Упаковка завершена")
            
            self.log("Orchestrator", "✨ Задача успешно завершена!")
            
            return {
                "success": True,
                "artifacts": self.artifacts,
                "iterations": self.current_iteration
            }
            
        except Exception as e:
            self.log("Orchestrator", f"❌ Критическая ошибка: {str(e)}", "ERROR")
            return {
                "success": False,
                "artifacts": self.artifacts,
                "error": str(e)
            }
