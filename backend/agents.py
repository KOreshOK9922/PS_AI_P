"""
Система агентов — Архитектор, Строитель, Исполнитель, Отладчик, Валидатор
"""

import json
import re
import asyncio
from typing import Callable, Any

from parser import fallback_parse
from plant_sim import PlantSimConnection
from ollama_client import OllamaClient


# ─── Prompt Templates ─────────────────────────────────────────────────

ARCHITECT_PROMPT = """Ты — архитектор моделей для Siemens Plant Simulation 2404.
Проанализируй описание производственной линии и верни JSON-спецификацию.

ВАЖНЫЕ ФАКТЫ О Plant Simulation 2404:
- Класс станции: Station (НЕ SingleProc!)
- Метод создания: derive (НЕ create!)
- Переименование: setName() (НЕ .name := !)
- Классы: Source, Station, Buffer, Drain, EventController
- Параметры: interval (сек), procTime (сек), capacity

Верни JSON в формате:
{
  "objects": [
    {"name": "SRC_1", "class": "Source", "params": {"interval": 180}},
    {"name": "ST_1", "class": "Station", "params": {"procTime": 20}},
    {"name": "BUF_1", "class": "Buffer", "params": {"capacity": 10}},
    {"name": "DRN_1", "class": "Drain", "params": {}}
  ],
  "connections": [["SRC_1", "ST_1"], ["ST_1", "BUF_1"], ["BUF_1", "DRN_1"]]
}

Описание: {description}

Верни ТОЛЬКО JSON, без пояснений."""

DEBUGGER_PROMPT = """Ты — отладчик SimTalk кода для Plant Simulation 2404.
Проанализируй ошибку и предложи исправление.

ВАЖНЫЕ ФАКТЫ:
- succ — только для чтения
- derive (не create)
- setName (не .name :=)
- Только двойные кавычки
- return только внутри методов

Ошибка: {error}
Код: {code}

Предложи исправленный код (только SimTalk, без пояснений)."""


# ─── Agent Swarm ──────────────────────────────────────────────────────

class AgentSwarm:
    def __init__(self, log_fn: Callable):
        self.log = log_fn
        self.architect = ArchitectAgent(log_fn)
        self.builder = BuilderAgent(log_fn)
        self.executor = ExecutorAgent(log_fn)
        self.debugger = DebuggerAgent(log_fn)
        self.validator = ValidatorAgent(log_fn)


# ─── Architect Agent ──────────────────────────────────────────────────

class ArchitectAgent:
    def __init__(self, log_fn: Callable):
        self.log = log_fn
    
    async def parse(self, description: str, ollama: OllamaClient) -> dict:
        """Парсит текстовое описание в JSON-спецификацию"""
        
        # Пробуем LLM
        try:
            if await ollama.check_health():
                self.log("INFO", "ARCHITECT", "Использую LLM для парсинга...")
                prompt = ARCHITECT_PROMPT.format(description=description)
                response = await ollama.generate(prompt)
                
                # Извлекаем JSON из ответа
                spec = self._extract_json(response)
                if spec and self._validate_spec(spec):
                    self.log("SUCCESS", "ARCHITECT", "LLM успешно распарсила описание")
                    return spec
                else:
                    self.log("WARN", "ARCHITECT", "LLM вернула невалидный JSON — переключаюсь на fallback")
        except Exception as e:
            self.log("WARN", "ARCHITECT", f"LLM недоступна: {e}")
        
        # Fallback: regex-парсер
        self.log("INFO", "PARSER", "Использую fallback regex-парсер...")
        spec = fallback_parse(description)
        
        if not spec["objects"]:
            self.log("ERROR", "PARSER", "Не удалось распарсить описание!")
            raise ValueError("Не удалось извлечь объекты из описания")
        
        self.log("SUCCESS", "PARSER", f"Fallback-парсер нашёл {len(spec['objects'])} объектов")
        return spec
    
    def _extract_json(self, text: str) -> dict | None:
        """Извлекает JSON из текста ответа LLM"""
        # Ищем JSON в markdown-блоке
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Ищем просто JSON-объект
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _validate_spec(self, spec: dict) -> bool:
        """Проверяет валидность спецификации"""
        if "objects" not in spec or "connections" not in spec:
            return False
        if not isinstance(spec["objects"], list) or len(spec["objects"]) == 0:
            return False
        for obj in spec["objects"]:
            if "name" not in obj or "class" not in obj:
                return False
            if obj["class"] not in ("Source", "Station", "Buffer", "Drain", "EventController"):
                return False
        return True


# ─── Builder Agent ────────────────────────────────────────────────────

class BuilderAgent:
    """Генерирует SimTalk код из JSON-спецификации"""
    
    def __init__(self, log_fn: Callable):
        self.log = log_fn
    
    def generate(self, spec: dict) -> list[dict]:
        """Генерирует блоки SimTalk кода"""
        blocks = []
        
        # 1. Создание EventController
        blocks.append({
            "type": "init",
            "code": """
var ec : object
ec := .MaterialFlow.EventController.derive(root)
ec.setName("EventController")
""",
        })
        
        # 2. Создание объектов
        for obj in spec["objects"]:
            class_name = obj["class"]
            obj_name = obj["name"]
            
            code = f"""
var obj_{obj_name} : object
obj_{obj_name} := .MaterialFlow.{class_name}.derive(root)
obj_{obj_name}.setName("{obj_name}")
"""
            blocks.append({
                "type": "create",
                "object": obj_name,
                "code": code,
            })
        
        # 3. Установка параметров
        for obj in spec["objects"]:
            params = obj.get("params", {})
            if params:
                param_lines = []
                for key, value in params.items():
                    param_lines.append(f'root.{obj["name"]}.{key} := {value}')
                
                blocks.append({
                    "type": "params",
                    "object": obj["name"],
                    "code": "\n".join(param_lines),
                })
        
        # 4. Соединения
        for conn in spec.get("connections", []):
            src, dst = conn[0], conn[1]
            
            # Пробуем несколько методов соединений
            methods = [
                f'root.{src}.succ := root.{dst}',
                f'root.{src}.connect(root.{dst})',
                f'root.{src}.connectTo(root.{dst})',
                f'.MaterialFlow.Connector.derive(root, "C_{src}_{dst}", root.{src}, root.{dst})',
            ]
            
            blocks.append({
                "type": "connect",
                "source": src,
                "target": dst,
                "methods": methods,
                "code": methods[0],  # Первый метод по умолчанию
            })
        
        self.log("INFO", "BUILDER", f"Сгенерировано {len(blocks)} блоков кода")
        return blocks


# ─── Executor Agent ───────────────────────────────────────────────────

class ExecutorAgent:
    """Выполняет SimTalk код в Plant Simulation"""
    
    def __init__(self, log_fn: Callable):
        self.log = log_fn
    
    async def execute(self, blocks: list[dict], ps: PlantSimConnection) -> dict:
        """Выполняет все блоки кода"""
        results = {"objects_created": [], "params_set": [], "connections": []}
        
        for block in blocks:
            if block["type"] == "init":
                success, error = ps.execute(block["code"])
                if success:
                    self.log("SUCCESS", "EXECUTOR", "EventController создан")
                else:
                    self.log("WARN", "EXECUTOR", f"EventController: {error}")
                await asyncio.sleep(0.1)
            
            elif block["type"] == "create":
                obj_name = block["object"]
                success, error = ps.execute(block["code"])
                if success:
                    results["objects_created"].append(obj_name)
                    self.log("SUCCESS", "EXECUTOR", f"Объект {obj_name} создан")
                else:
                    self.log("ERROR", "EXECUTOR", f"Ошибка создания {obj_name}: {error}")
                await asyncio.sleep(0.1)
            
            elif block["type"] == "params":
                obj_name = block["object"]
                success, error = ps.execute(block["code"])
                if success:
                    results["params_set"].append(obj_name)
                    self.log("SUCCESS", "EXECUTOR", f"Параметры {obj_name} установлены")
                else:
                    self.log("WARN", "EXECUTOR", f"Параметры {obj_name}: {error}")
                await asyncio.sleep(0.1)
            
            elif block["type"] == "connect":
                src = block["source"]
                dst = block["target"]
                methods = block["methods"]
                
                connected = False
                for method in methods:
                    success, error = ps.execute(method)
                    if success:
                        connected = True
                        results["connections"].append({"source": src, "target": dst, "success": True, "method": method})
                        self.log("SUCCESS", "EXECUTOR", f"Соединение {src} → {dst} создано")
                        break
                    else:
                        self.log("RESEARCH", "EXECUTOR", f"Метод не сработал: {method[:50]}... → {error[:60]}")
                    await asyncio.sleep(0.1)
                
                if not connected:
                    results["connections"].append({"source": src, "target": dst, "success": False})
                    self.log("ERROR", "EXECUTOR", f"Не удалось соединить {src} → {dst}")
        
        results["all_connected"] = all(c.get("success") for c in results["connections"])
        return results
    
    async def retry_connections(self, found_method: dict, ps: PlantSimConnection) -> list[dict]:
        """Повторяет соединения найденным методом"""
        results = []
        # TODO: реализовать повторные соединения
        return results


# ─── Debugger Agent ───────────────────────────────────────────────────

class DebuggerAgent:
    """Анализирует ошибки и предлагает исправления"""
    
    def __init__(self, log_fn: Callable):
        self.log = log_fn
    
    async def debug(self, error: str, code: str, ollama: OllamaClient) -> str | None:
        """Анализирует ошибку и возвращает исправленный код"""
        try:
            if not await ollama.check_health():
                return None
            
            prompt = DEBUGGER_PROMPT.format(error=error, code=code)
            response = await ollama.generate(prompt)
            
            # Извлекаем код из ответа
            code_match = re.search(r'```(?:simtalk)?\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            
            # Может быть просто код
            lines = response.strip().split('\n')
            if any(':=' in line or 'derive' in line for line in lines):
                return response.strip()
            
        except Exception as e:
            self.log("WARN", "DEBUGGER", f"Ошибка отладки: {e}")
        
        return None


# ─── Validator Agent ──────────────────────────────────────────────────

class ValidatorAgent:
    """Сохраняет и проверяет модель"""
    
    def __init__(self, log_fn: Callable):
        self.log = log_fn
    
    async def save(self, ps: PlantSimConnection) -> bool:
        """Сохраняет модель"""
        save_path = r"C:\ProgramData\Siemens\PS_AI_Agent\model.spp"
        success, error = ps.save_model(save_path)
        if success:
            self.log("SUCCESS", "VALIDATOR", f"Модель сохранена: {save_path}")
            return True
        else:
            self.log("ERROR", "VALIDATOR", f"Ошибка сохранения: {error}")
            return False
