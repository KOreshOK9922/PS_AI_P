"""
Агенты мультиагентной системы
"""

from typing import Callable, Optional
from llm_client import OllamaClient


class ProductAnalyst:
    """Продуктовый аналитик - формализует требования"""
    
    def __init__(self, llm: OllamaClient, log_fn: Callable):
        self.llm = llm
        self.log = log_fn
    
    async def analyze(self, requirement: str) -> str:
        """Анализирует требование и создаёт документ requirements.md"""
        self.log("Product Analyst", "📊 Анализ требований...")
        
        system_prompt = """Ты - продуктовый аналитик. Твоя задача - формализовать требования пользователя.

Создай документ requirements.md со следующей структурой:

# Требования

## Обзор
Краткое описание проекта

## User Stories
Список пользовательских историй в формате:
- Как [роль], я хочу [действие], чтобы [цель]

## Функциональные требования
Список функциональных требований

## Нефункциональные требования
Производительность, безопасность, масштабируемость

## Edge Cases
Граничные случаи и обработка ошибок

## Критерии приёмки
Чёткие критерии завершения

Отвечай только содержимым файла, без пояснений."""
        
        prompt = f"Требование пользователя:\n\n{requirement}\n\nСоздай документ requirements.md"
        
        try:
            result = await self.llm.generate(prompt, system=system_prompt, temperature=0.2)
            self.log("Product Analyst", f"✅ Создан requirements.md ({len(result)} символов)")
            return result
        except Exception as e:
            self.log("Product Analyst", f"❌ Ошибка: {str(e)}", "ERROR")
            raise


class SystemArchitect:
    """Системный архитектор - проектирует архитектуру"""
    
    def __init__(self, llm: OllamaClient, log_fn: Callable):
        self.llm = llm
        self.log = log_fn
    
    async def design(self, requirements: str) -> str:
        """Проектирует архитектуру на основе требований"""
        self.log("System Architect", "🏛️ Проектирование архитектуры...")
        
        system_prompt = """Ты - системный архитектор. Твоя задача - спроектировать архитектуру решения.

Создай документ architecture.md со следующей структурой:

# Архитектура

## Технологический стек
Выбор языков, фреймворков, баз данных с обоснованием

## Структура проекта
Директории и модули

## Компоненты
Основные компоненты и их взаимодействие

## API Контракты
Описание API endpoints (если применимо)

## Схема данных
Модели данных и связи

## Паттерны проектирования
Используемые паттерны (SOLID, DRY, KISS)

Отвечай только содержимым файла, без пояснений."""
        
        prompt = f"Требования:\n\n{requirements}\n\nСоздай документ architecture.md"
        
        try:
            result = await self.llm.generate(prompt, system=system_prompt, temperature=0.2)
            self.log("System Architect", f"✅ Создан architecture.md ({len(result)} символов)")
            return result
        except Exception as e:
            self.log("System Architect", f"❌ Ошибка: {str(e)}", "ERROR")
            raise


class LeadEngineer:
    """Ведущий разработчик - реализует код"""
    
    def __init__(self, llm: OllamaClient, log_fn: Callable):
        self.llm = llm
        self.log = log_fn
    
    async def implement(
        self,
        requirements: str,
        architecture: str,
        review_feedback: Optional[dict] = None
    ) -> dict:
        """Реализует код по спецификациям"""
        self.log("Lead Engineer", "💻 Реализация кода...")
        
        system_prompt = """Ты - ведущий разработчик. Твоя задача - реализовать код по спецификациям.

Требования к коду:
- Соответствие SOLID, DRY, KISS принципам
- Типизация (где применимо)
- Документация (docstrings, комментарии)
- Модульность
- Обработка ошибок

Верни JSON в формате:
{
  "files": [
    {
      "path": "путь/к/файлу.py",
      "content": "содержимое файла"
    }
  ],
  "main_file": "путь/к/главному/файлу.py",
  "description": "краткое описание реализации"
}

Отвечай только JSON, без пояснений."""
        
        prompt = f"Требования:\n\n{requirements}\n\nАрхитектура:\n\n{architecture}"
        
        if review_feedback:
            prompt += f"\n\nЗамечания ревьюера (исправь их):\n\n{review_feedback}"
        
        try:
            result = await self.llm.generate(prompt, system=system_prompt, temperature=0.2)
            
            # Парсим JSON
            import json
            import re
            
            # Ищем JSON в ответе
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                code_data = json.loads(json_match.group(0))
                self.log("Lead Engineer", f"✅ Реализовано {len(code_data.get('files', []))} файлов")
                return code_data
            else:
                raise ValueError("Не удалось извлечь JSON из ответа")
                
        except Exception as e:
            self.log("Lead Engineer", f"❌ Ошибка: {str(e)}", "ERROR")
            raise


class QAEngineer:
    """QA инженер - тестирует код"""
    
    def __init__(self, llm: OllamaClient, log_fn: Callable):
        self.llm = llm
        self.log = log_fn
    
    async def test(self, code: dict, requirements: str) -> dict:
        """Тестирует код"""
        self.log("QA Engineer", "🧪 Тестирование кода...")
        
        system_prompt = """Ты - QA инженер. Твоя задача - протестировать код и написать тесты.

Создай тесты для кода и проверь его на соответствие требованиям.

Верни JSON в формате:
{
  "passed": true/false,
  "tests": [
    {
      "name": "название теста",
      "status": "passed/failed",
      "message": "описание"
    }
  ],
  "coverage": 85,
  "test_files": [
    {
      "path": "путь/к/тесту.py",
      "content": "содержимое теста"
    }
  ],
  "failures": ["список проблем если есть"]
}

Отвечай только JSON, без пояснений."""
        
        prompt = f"Код:\n\n{code}\n\nТребования:\n\n{requirements}"
        
        try:
            result = await self.llm.generate(prompt, system=system_prompt, temperature=0.2)
            
            # Парсим JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                test_result = json.loads(json_match.group(0))
                
                if test_result.get("passed"):
                    self.log("QA Engineer", f"✅ Все тесты пройдены (покрытие: {test_result.get('coverage', 0)}%)")
                else:
                    self.log("QA Engineer", f"❌ Тесты не пройдены", "WARN")
                
                return test_result
            else:
                raise ValueError("Не удалось извлечь JSON из ответа")
                
        except Exception as e:
            self.log("QA Engineer", f"❌ Ошибка: {str(e)}", "ERROR")
            raise


class CodeReviewer:
    """Ревьюер кода - проверяет качество"""
    
    def __init__(self, llm: OllamaClient, log_fn: Callable):
        self.llm = llm
        self.log = log_fn
    
    async def review(self, code: dict, architecture: str) -> dict:
        """Ревьюит код"""
        self.log("Code Reviewer", "🔍 Ревью кода...")
        
        system_prompt = """Ты - ревьюер кода и security аудитор. Твоя задача - проверить код на качество и безопасность.

Проверь:
- Соответствие архитектуре
- SOLID, DRY, KISS принципы
- Обработка ошибок
- Безопасность (OWASP Top-10)
- Читаемость и документация
- Производительность

Верни JSON в формате:
{
  "approved": true/false,
  "score": 85,
  "issues": [
    {
      "severity": "critical/major/minor",
      "file": "путь/к/файлу",
      "line": 10,
      "description": "описание проблемы",
      "suggestion": "предложение по исправлению"
    }
  ],
  "summary": "общее резюме"
}

Отвечай только JSON, без пояснений."""
        
        prompt = f"Код:\n\n{code}\n\nАрхитектура:\n\n{architecture}"
        
        try:
            result = await self.llm.generate(prompt, system=system_prompt, temperature=0.2)
            
            # Парсим JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                review_result = json.loads(json_match.group(0))
                
                if review_result.get("approved"):
                    self.log("Code Reviewer", f"✅ Код одобрен (оценка: {review_result.get('score', 0)}/100)")
                else:
                    issues = review_result.get("issues", [])
                    critical = sum(1 for i in issues if i.get("severity") == "critical")
                    self.log("Code Reviewer", f"❌ Код не одобрен ({critical} критических замечаний)", "WARN")
                
                return review_result
            else:
                raise ValueError("Не удалось извлечь JSON из ответа")
                
        except Exception as e:
            self.log("Code Reviewer", f"❌ Ошибка: {str(e)}", "ERROR")
            raise


class DevOpsEngineer:
    """DevOps инженер - упаковывает приложение"""
    
    def __init__(self, llm: OllamaClient, log_fn: Callable):
        self.llm = llm
        self.log = log_fn
    
    async def package(self, code: dict, requirements: str, architecture: str) -> dict:
        """Создаёт Docker и CI/CD конфигурацию"""
        self.log("DevOps Engineer", "🚀 Упаковка приложения...")
        
        system_prompt = """Ты - DevOps инженер. Твоя задача - создать конфигурацию для упаковки и доставки приложения.

Создай:
1. Dockerfile для контейнеризации
2. docker-compose.yml для локальной разработки
3. CI/CD конфигурацию (GitHub Actions)
4. .env.example с переменными окружения

Верни JSON в формате:
{
  "Dockerfile": "содержимое Dockerfile",
  "docker-compose.yml": "содержимое docker-compose.yml",
  "ci.yml": "содержимое GitHub Actions workflow",
  ".env.example": "содержимое .env.example",
  "README.md": "инструкция по развёртыванию"
}

Отвечай только JSON, без пояснений."""
        
        prompt = f"Код:\n\n{code}\n\nТребования:\n\n{requirements}\n\nАрхитектура:\n\n{architecture}"
        
        try:
            result = await self.llm.generate(prompt, system=system_prompt, temperature=0.2)
            
            # Парсим JSON
            import json
            import re
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                package_result = json.loads(json_match.group(0))
                self.log("DevOps Engineer", "✅ Упаковка завершена")
                return package_result
            else:
                raise ValueError("Не удалось извлечь JSON из ответа")
                
        except Exception as e:
            self.log("DevOps Engineer", f"❌ Ошибка: {str(e)}", "ERROR")
            raise
