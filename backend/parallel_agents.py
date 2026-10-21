"""
Система параллельных агентов для решения задач Plant Simulation

Архитектура:
- Supervisor Agent: координирует работу, распределяет задачи
- Architect Agent: парсит описание, генерирует JSON-спецификацию
- Builder Agent: генерирует SimTalk код
- Executor Agent: выполняет код через COM
- Debugger Agent: анализирует ошибки, ищет решения
- Researcher Agent: исследует API, тестирует методы
- Validator Agent: проверяет корректность модели
"""

import asyncio
import json
import re
import time
from typing import Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from knowledge_base import kb


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    DONE = "done"
    ERROR = "error"
    WAITING = "waiting"


@dataclass
class AgentResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


class BaseAgent:
    """Базовый класс для всех агентов"""
    
    def __init__(self, name: str, log_fn: Callable):
        self.name = name
        self.log = log_fn
        self.status = AgentStatus.IDLE
        self.last_result: Optional[AgentResult] = None
    
    async def execute(self, *args, **kwargs) -> AgentResult:
        """Выполняет задачу агента"""
        self.status = AgentStatus.WORKING
        start_time = time.time()
        
        try:
            result = await self._run(*args, **kwargs)
            self.last_result = result
            self.status = AgentStatus.DONE if result.success else AgentStatus.ERROR
            return result
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.last_result = AgentResult(success=False, error=str(e))
            return self.last_result
        finally:
            self.last_result.execution_time = time.time() - start_time
    
    async def _run(self, *args, **kwargs) -> AgentResult:
        """Переопределяется в наследниках"""
        raise NotImplementedError


class ArchitectAgent(BaseAgent):
    """Агент-архитектор: парсит описание в JSON-спецификацию"""
    
    def __init__(self, log_fn: Callable, ollama_client=None):
        super().__init__("Architect", log_fn)
        self.ollama = ollama_client
    
    async def _run(self, description: str) -> AgentResult:
        self.log("INFO", self.name, "Начало парсинга описания")
        
        # Попытка 1: LLM
        if self.ollama:
            try:
                spec = await self._parse_with_llm(description)
                if spec and self._validate_spec(spec):
                    self.log("SUCCESS", self.name, f"LLM распарсила: {len(spec['objects'])} объектов")
                    return AgentResult(success=True, data=spec)
            except Exception as e:
                self.log("WARN", self.name, f"LLM недоступна: {e}")
        
        # Попытка 2: Fallback regex
        self.log("INFO", self.name, "Использование fallback-парсера")
        spec = self._parse_with_regex(description)
        
        if not spec['objects']:
            return AgentResult(success=False, error="Не удалось извлечь объекты")
        
        self.log("SUCCESS", self.name, f"Fallback нашёл {len(spec['objects'])} объектов")
        return AgentResult(success=True, data=spec)
    
    async def _parse_with_llm(self, description: str) -> Optional[dict]:
        """Парсинг через LLM"""
        if not self.ollama:
            return None
        
        prompt = f"""Ты — архитектор моделей для Siemens Plant Simulation 2404.
Проанализируй описание и верни JSON-спецификацию.

ПРАВИЛА:
- Классы: Source, Station, Buffer, Drain, ParallelStation
- Метод создания: createObject(frame, x, y)
- Соединения: Connector.connect(obj1, obj2)
- Расположи объекты слева направо с шагом 120 по X

Верни JSON:
{{
  "objects": [
    {{"name": "SRC_1", "class": "Source", "x": 100, "y": 100, "params": {{"interval": 180}}}}
  ],
  "connections": [["SRC_1", "ST_1"]]
}}

Описание: {description}

Верни ТОЛЬКО JSON."""
        
        response = await self.ollama.generate(prompt)
        
        # Извлекаем JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        return None
    
    def _parse_with_regex(self, description: str) -> dict:
        """Fallback парсинг через regex"""
        objects = []
        connections = []
        desc_lower = description.lower()
        x_pos = 100
        y_pos = 100
        x_step = 120
        
        # Источник
        if re.search(r'источник|source|генератор', desc_lower):
            obj = {
                "name": "SRC_1",
                "class": "Source",
                "x": x_pos,
                "y": y_pos,
                "params": {}
            }
            
            interval = self._extract_time(description, r'интервал[а-я]*\s*(\d+)\s*(мин|сек|s|min)?')
            if interval:
                obj["params"]["interval"] = interval
            
            objects.append(obj)
            x_pos += x_step
        
        # Станция
        station_matches = list(re.finditer(r'станци[яий]|station|обработк', desc_lower))
        for i, match in enumerate(station_matches):
            name = f"ST_{i+1}" if i > 0 else "ST_1"
            obj = {
                "name": name,
                "class": "Station",
                "x": x_pos,
                "y": y_pos,
                "params": {}
            }
            
            proc = self._extract_time(description, r'(?:обработк|время)\s*(\d+)\s*(мин|сек|s|min)?')
            if proc:
                obj["params"]["procTime"] = proc
            
            objects.append(obj)
            x_pos += x_step
        
        # Буфер
        if re.search(r'накопител|буфер|buffer', desc_lower):
            obj = {
                "name": "BUF_1",
                "class": "Buffer",
                "x": x_pos,
                "y": y_pos,
                "params": {}
            }
            
            cap_match = re.search(r'(?:на\s+)?(\d+)\s*(?:мест|шт)', description, re.I)
            if cap_match:
                obj["params"]["capacity"] = int(cap_match.group(1))
            
            objects.append(obj)
            x_pos += x_step
        
        # Сход
        if re.search(r'сход|drain|выход', desc_lower):
            objects.append({
                "name": "DRN_1",
                "class": "Drain",
                "x": x_pos,
                "y": y_pos,
                "params": {}
            })
        
        # Соединения
        for i in range(len(objects) - 1):
            connections.append([objects[i]["name"], objects[i+1]["name"]])
        
        return {"objects": objects, "connections": connections}
    
    def _extract_time(self, text: str, pattern: str) -> Optional[int]:
        """Извлекает время и конвертирует в секунды"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower() if match.group(2) else "сек"
            if unit in ["мин", "min"]:
                return value * 60
            return value
        return None
    
    def _validate_spec(self, spec: dict) -> bool:
        """Проверка валидности спецификации"""
        if "objects" not in spec or "connections" not in spec:
            return False
        for obj in spec["objects"]:
            if not all(k in obj for k in ["name", "class", "x", "y"]):
                return False
        return True


class BuilderAgent(BaseAgent):
    """Агент-строитель: генерирует SimTalk код"""
    
    def __init__(self, log_fn: Callable):
        super().__init__("Builder", log_fn)
    
    async def _run(self, spec: dict) -> AgentResult:
        self.log("INFO", self.name, "Генерация SimTalk кода")
        
        code_lines = []
        
        # Объявление фрейма
        code_lines.append('var f : object')
        code_lines.append('f := .Models.Model')
        code_lines.append('')
        
        # Создание объектов
        for obj in spec["objects"]:
            class_name = obj["class"]
            obj_name = obj["name"]
            x = obj["x"]
            y = obj["y"]
            
            # Получаем информацию о классе из базы знаний
            class_info = kb.get_object_class_info(class_name)
            if class_info:
                create_method = class_info["create_method"]
            else:
                create_method = f".MaterialFlow.{class_name}.createObject(f, {x}, {y})"
            
            code_lines.append(f'var {obj_name} : object')
            code_lines.append(f'{obj_name} := {create_method}')
            code_lines.append(f'{obj_name}.setName("{obj_name}")')
            code_lines.append('')
        
        # Установка параметров
        for obj in spec["objects"]:
            params = obj.get("params", {})
            for key, value in params.items():
                code_lines.append(f'f.{obj["name"]}.{key} := {value}')
        
        if any(obj.get("params") for obj in spec["objects"]):
            code_lines.append('')
        
        # Создание соединений
        for conn in spec["connections"]:
            src, dst = conn[0], conn[1]
            code_lines.append(f'.MaterialFlow.Connector.connect(f.{src}, f.{dst})')
        
        code = '\n'.join(code_lines)
        
        self.log("SUCCESS", self.name, f"Сгенерировано {len(code_lines)} строк кода")
        return AgentResult(success=True, data=code)


class ExecutorAgent(BaseAgent):
    """Агент-исполнитель: выполняет код через COM"""
    
    def __init__(self, log_fn: Callable, plant_sim):
        super().__init__("Executor", log_fn)
        self.ps = plant_sim
    
    async def _run(self, code: str, max_attempts: int = 3) -> AgentResult:
        self.log("INFO", self.name, "Выполнение кода")
        
        for attempt in range(1, max_attempts + 1):
            self.log("INFO", self.name, f"Попытка {attempt}/{max_attempts}")
            
            self.ps.new_model()
            success, error = self.ps.execute(code)
            
            if success:
                self.log("SUCCESS", self.name, "Код выполнен успешно")
                kb.record_attempt("execute_code", True)
                return AgentResult(success=True)
            else:
                self.log("ERROR", self.name, f"Ошибка: {error}")
                kb.record_attempt("execute_code", False)
                kb.record_error(error)
                
                # Ищем решение в базе знаний
                solution = kb.find_similar_error(error)
                if solution and solution.get("solution"):
                    self.log("INFO", self.name, f"Найдено решение: {solution['solution']}")
                    # TODO: применить решение
                
                if attempt < max_attempts:
                    await asyncio.sleep(1)
        
        return AgentResult(success=False, error="Все попытки неудачны")


class DebuggerAgent(BaseAgent):
    """Агент-отладчик: анализирует ошибки и ищет решения"""
    
    def __init__(self, log_fn: Callable, ollama_client=None):
        super().__init__("Debugger", log_fn)
        self.ollama = ollama_client
    
    async def _run(self, error: str, code: str) -> AgentResult:
        self.log("INFO", self.name, "Анализ ошибки")
        
        # Проверяем базу знаний
        solution = kb.find_similar_error(error)
        if solution and solution.get("solution"):
            self.log("SUCCESS", self.name, f"Решение найдено в БЗ: {solution['solution']}")
            return AgentResult(success=True, data=solution["solution"])
        
        # Если LLM доступна, пробуем её
        if self.ollama:
            try:
                fixed_code = await self._debug_with_llm(error, code)
                if fixed_code:
                    self.log("SUCCESS", self.name, "LLM предложила исправление")
                    kb.record_error(error, fixed_code)
                    return AgentResult(success=True, data=fixed_code)
            except Exception as e:
                self.log("WARN", self.name, f"LLM недоступна: {e}")
        
        # Генерируем варианты исправлений
        alternatives = self._generate_alternatives(error, code)
        if alternatives:
            self.log("INFO", self.name, f"Сгенерировано {len(alternatives)} альтернатив")
            return AgentResult(success=True, data=alternatives)
        
        return AgentResult(success=False, error="Не удалось найти решение")
    
    async def _debug_with_llm(self, error: str, code: str) -> Optional[str]:
        """Отладка через LLM"""
        if not self.ollama:
            return None
        
        prompt = f"""Ты — отладчик SimTalk кода для Plant Simulation 2404.
Проанализируй ошибку и предложи исправление.

ПРАВИЛА:
- createObject(f, x, y) — создание объектов
- Connector.connect(obj1, obj2) — соединения
- setName() — переименование
- Только двойные кавычки

Ошибка: {error}
Код: {code}

Предложи исправленный код (только SimTalk)."""
        
        response = await self.ollama.generate(prompt)
        
        # Извлекаем код
        code_match = re.search(r'```(?:simtalk)?\s*(.*?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        return None
    
    def _generate_alternatives(self, error: str, code: str) -> list[str]:
        """Генерирует альтернативные варианты кода"""
        alternatives = []
        
        # Анализ типа ошибки
        if "Unknown identifier" in error:
            # Пробуем разные варианты создания
            if "createObject" in code:
                alternatives.append(code.replace("createObject", "derive"))
            elif "derive" in code:
                alternatives.append(code.replace("derive", "createObject"))
        
        elif "cannot assign" in error:
            # Пробуем разные методы соединений
            if ".succ :=" in code:
                alternatives.append(code.replace(".succ :=", ".Connector.connect"))
        
        elif "Incompatible types" in error:
            # Пробуем разные типы аргументов
            alternatives.append(code)  # TODO: улучшить
        
        return alternatives


class ResearcherAgent(BaseAgent):
    """Агент-исследователь: тестирует методы API"""
    
    def __init__(self, log_fn: Callable, plant_sim):
        super().__init__("Researcher", log_fn)
        self.ps = plant_sim
    
    async def _run(self, task: str = "full") -> AgentResult:
        self.log("INFO", self.name, f"Запуск исследования: {task}")
        
        if task == "full":
            return await self._full_research()
        elif task == "connections":
            return await self._research_connections()
        elif task == "classes":
            return await self._research_classes()
        else:
            return AgentResult(success=False, error=f"Неизвестная задача: {task}")
    
    async def _full_research(self) -> AgentResult:
        """Полное исследование API"""
        results = []
        
        # Тест 1: Создание объектов
        self.log("INFO", self.name, "Тест 1: Создание объектов")
        success = await self._test_create_methods()
        results.append(("create", success))
        
        # Тест 2: Соединения
        self.log("INFO", self.name, "Тест 2: Методы соединений")
        success = await self._test_connection_methods()
        results.append(("connect", success))
        
        # Тест 3: Параметры
        self.log("INFO", self.name, "Тест 3: Установка параметров")
        success = await self._test_parameters()
        results.append(("params", success))
        
        self.log("SUCCESS", self.name, f"Исследование завершено: {len(results)} тестов")
        return AgentResult(success=True, data=results)
    
    async def _test_create_methods(self) -> bool:
        """Тестирует методы создания объектов"""
        methods = [
            ("createObject", ".MaterialFlow.Source.createObject(f, 100, 100)"),
            ("derive", ".MaterialFlow.Source.derive(f)"),
        ]
        
        for name, code in methods:
            full_code = f"""
var f : object
f := .Models.Model
var obj : object
obj := {code}
"""
            success, error, elapsed = self.ps.test_method(full_code)
            kb.record_attempt(name, success)
            
            if success:
                self.log("SUCCESS", self.name, f"✅ {name} работает")
                return True
            else:
                self.log("INFO", self.name, f"❌ {name}: {error[:50]}")
        
        return False
    
    async def _test_connection_methods(self) -> bool:
        """Тестирует методы соединений"""
        methods = [
            ("Connector.connect", ".MaterialFlow.Connector.connect(obj1, obj2)"),
            ("succ :=", "obj1.succ := obj2"),
            ("connect()", "obj1.connect(obj2)"),
        ]
        
        for name, code in methods:
            full_code = f"""
var f : object
f := .Models.Model
var obj1 : object
obj1 := .MaterialFlow.Source.createObject(f, 100, 100)
var obj2 : object
obj2 := .MaterialFlow.Station.createObject(f, 220, 100)
{code}
"""
            success, error, elapsed = self.ps.test_method(full_code)
            kb.record_attempt(name, success)
            
            if success:
                self.log("SUCCESS", self.name, f"✅ {name} работает")
                return True
            else:
                self.log("INFO", self.name, f"❌ {name}: {error[:50]}")
        
        return False
    
    async def _test_parameters(self) -> bool:
        """Тестирует установку параметров"""
        tests = [
            ("interval", "f.SRC.interval := 120"),
            ("procTime", "f.ST.procTime := 15"),
        ]
        
        for name, code in tests:
            full_code = f"""
var f : object
f := .Models.Model
var SRC : object
SRC := .MaterialFlow.Source.createObject(f, 100, 100)
var ST : object
ST := .MaterialFlow.Station.createObject(f, 220, 100)
{code}
"""
            success, error, elapsed = self.ps.test_method(full_code)
            kb.record_attempt(name, success)
            
            if success:
                self.log("SUCCESS", self.name, f"✅ {name} работает")
            else:
                self.log("INFO", self.name, f"❌ {name}: {error[:50]}")
        
        return True


class ValidatorAgent(BaseAgent):
    """Агент-валидатор: проверяет корректность модели"""
    
    def __init__(self, log_fn: Callable, plant_sim):
        super().__init__("Validator", log_fn)
        self.ps = plant_sim
    
    async def _run(self, spec: dict) -> AgentResult:
        self.log("INFO", self.name, "Валидация модели")
        
        # Создаём DataTable для подсчёта
        count_code = f"""
var f : object
f := .Models.Model

var dt : object
dt := .InformationFlow.DataTable.createObject(f, "VALIDATION_TABLE")

var count : integer
count := f.numObjects

dt.setCell(1, 1, count)
"""
        success, error = self.ps.execute(count_code)
        if not success:
            self.log("ERROR", self.name, f"Ошибка создания таблицы: {error}")
            return AgentResult(success=False, error=error)
        
        # Читаем количество объектов
        try:
            actual_count = self.ps.app.GetTableCell(".Models.Model.VALIDATION_TABLE", 1, 1)
            expected_count = len(spec["objects"])
            
            if actual_count != expected_count:
                self.log("ERROR", self.name, f"Ожидалось {expected_count}, найдено {actual_count}")
                return AgentResult(success=False, error="Неверное количество объектов")
            
            self.log("SUCCESS", self.name, f"Найдено {actual_count} объектов")
            
            # Удаляем таблицу
            self.ps.execute(".Models.Model.VALIDATION_TABLE.deleteObject")
            
            return AgentResult(success=True)
            
        except Exception as e:
            self.log("ERROR", self.name, f"Ошибка чтения: {e}")
            return AgentResult(success=False, error=str(e))


class SupervisorAgent:
    """Агент-супервизор: координирует работу всех агентов"""
    
    def __init__(self, log_fn: Callable, plant_sim, ollama_client=None):
        self.log = log_fn
        self.ps = plant_sim
        self.ollama = ollama_client
        
        # Создаём агентов
        self.architect = ArchitectAgent(log_fn, ollama_client)
        self.builder = BuilderAgent(log_fn)
        self.executor = ExecutorAgent(log_fn, plant_sim)
        self.debugger = DebuggerAgent(log_fn, ollama_client)
        self.researcher = ResearcherAgent(log_fn, plant_sim)
        self.validator = ValidatorAgent(log_fn, plant_sim)
    
    async def run_pipeline(self, description: str) -> dict:
        """Запускает полный конвейер обработки"""
        self.log("INFO", "Supervisor", "Запуск конвейера")
        
        results = {}
        
        # Фаза 1: Парсинг (параллельно с исследованием если нужно)
        self.log("INFO", "Supervisor", "Фаза 1: Парсинг описания")
        arch_result = await self.architect.execute(description)
        results["architect"] = arch_result
        
        if not arch_result.success:
            return {"success": False, "error": "Ошибка парсинга", "results": results}
        
        spec = arch_result.data
        
        # Фаза 2: Генерация кода
        self.log("INFO", "Supervisor", "Фаза 2: Генерация кода")
        build_result = await self.builder.execute(spec)
        results["builder"] = build_result
        
        if not build_result.success:
            return {"success": False, "error": "Ошибка генерации", "results": results}
        
        code = build_result.data
        
        # Фаза 3: Выполнение (с возможной отладкой)
        self.log("INFO", "Supervisor", "Фаза 3: Выполнение кода")
        exec_result = await self.executor.execute(code)
        results["executor"] = exec_result
        
        if not exec_result.success:
            # Запускаем отладку
            self.log("WARN", "Supervisor", "Запуск отладки")
            debug_result = await self.debugger.execute(exec_result.error, code)
            results["debugger"] = debug_result
            
            if debug_result.success and isinstance(debug_result.data, str):
                # Пробуем исправленный код
                self.log("INFO", "Supervisor", "Попытка с исправленным кодом")
                exec_result = await self.executor.execute(debug_result.data)
                results["executor_retry"] = exec_result
        
        if not exec_result.success:
            return {"success": False, "error": "Ошибка выполнения", "results": results}
        
        # Фаза 4: Валидация
        self.log("INFO", "Supervisor", "Фаза 4: Валидация")
        valid_result = await self.validator.execute(spec)
        results["validator"] = valid_result
        
        if not valid_result.success:
            return {"success": False, "error": "Ошибка валидации", "results": results}
        
        self.log("SUCCESS", "Supervisor", "Конвейер завершён успешно")
        return {"success": True, "spec": spec, "code": code, "results": results}
    
    async def run_parallel_research(self) -> dict:
        """Запускает параллельное исследование"""
        self.log("INFO", "Supervisor", "Запуск параллельного исследования")
        
        # Запускаем все исследования параллельно
        tasks = [
            self.researcher.execute("connections"),
            self.researcher.execute("classes"),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "success": all(r.success for r in results if isinstance(r, AgentResult)),
            "results": [r.data if isinstance(r, AgentResult) else str(r) for r in results]
        }
