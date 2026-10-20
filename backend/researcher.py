"""
Авто-исследователь API Plant Simulation 2404

Автоматически пробует все известные методы создания соединений,
тестирует новые комбинации, интроспекция атрибутов.
"""

import asyncio
import time
from typing import Callable, Optional

from plant_sim import PlantSimConnection


class APIResearcher:
    """Авто-исследователь API Plant Simulation"""
    
    def __init__(self, log_fn: Callable, ps: PlantSimConnection):
        self.log = log_fn
        self.ps = ps
        self.results: list[dict] = []
        self.known_working: list[dict] = []
        self.known_broken: list[dict] = []
    
    async def full_research(self):
        """Полное исследование API"""
        self.log("INFO", "RESEARCHER", "=== НАЧАЛО ИССЛЕДОВАНИЯ API ===")
        
        # 1. Проверка подключения
        await self._step("Проверка подключения", self._check_connection)
        
        # 2. Создание тестовых объектов
        await self._step("Создание тестовых объектов", self._create_test_objects)
        
        # 3. Тестирование всех известных методов соединений
        await self._step("Тестирование методов соединений", self._test_connection_methods)
        
        # 4. Интроспекция атрибутов
        await self._step("Интроспекция атрибутов объектов", self._introspect_attributes)
        
        # 5. Тестирование параметров
        await self._step("Тестирование параметров", self._test_parameters)
        
        # 6. Тестирование создания объектов
        await self._step("Тестирование классов объектов", self._test_object_classes)
        
        # 7. Экспериментальные методы (LLM-генерация)
        await self._step("Экспериментальные методы", self._experimental_methods)
        
        # 8. Очистка
        await self._step("Очистка тестовых объектов", self._cleanup)
        
        self.log("INFO", "RESEARCHER", f"=== ИССЛЕДОВАНИЕ ЗАВЕРШЕНО ===")
        self.log("INFO", "RESEARCHER", f"Рабочих: {len(self.known_working)}, Нерабочих: {len(self.known_broken)}")
    
    async def find_connection_method(self) -> Optional[dict]:
        """Ищет рабочий метод создания соединений"""
        self.log("INFO", "RESEARCHER", "Поиск рабочего метода соединений...")
        
        # Создаём тестовые объекты
        success, error = self.ps.create_test_objects()
        if not success:
            self.log("ERROR", "RESEARCHER", f"Не удалось создать тестовые объекты: {error}")
            return None
        
        # Пробуем все известные методы
        methods = self._get_connection_methods()
        
        for method_info in methods:
            name = method_info["name"]
            code = method_info["code"]
            
            self.log("RESEARCH", "RESEARCHER", f"Пробую: {name}")
            success, error, elapsed = self.ps.test_method(code)
            
            result = {
                "method": name,
                "code": code,
                "success": success,
                "error": error if not success else None,
                "time": round(elapsed),
            }
            self.results.append(result)
            
            if success:
                self.known_working.append(result)
                self.log("SUCCESS", "RESEARCHER", f"✅ РАБОЧИЙ МЕТОД: {name}")
                self.ps.cleanup_test_objects()
                return result
            else:
                self.known_broken.append(result)
                self.log("RESEARCH", "RESEARCHER", f"❌ {name}: {error[:80]}")
            
            await asyncio.sleep(0.1)
        
        # Пересоздаём объекты для следующего раунда
        self.ps.cleanup_test_objects()
        self.ps.create_test_objects()
        
        # Пробуем дополнительные методы
        extra_methods = self._get_extra_connection_methods()
        for method_info in extra_methods:
            name = method_info["name"]
            code = method_info["code"]
            
            self.log("RESEARCH", "RESEARCHER", f"Доп. метод: {name}")
            success, error, elapsed = self.ps.test_method(code)
            
            result = {
                "method": name,
                "code": code,
                "success": success,
                "error": error if not success else None,
                "time": round(elapsed),
            }
            self.results.append(result)
            
            if success:
                self.known_working.append(result)
                self.log("SUCCESS", "RESEARCHER", f"✅ НАЙДЕН: {name}")
                self.ps.cleanup_test_objects()
                return result
            else:
                self.known_broken.append(result)
            
            await asyncio.sleep(0.1)
        
        self.ps.cleanup_test_objects()
        self.log("WARN", "RESEARCHER", "Рабочий метод соединений НЕ найден")
        return None
    
    async def _step(self, name: str, fn):
        """Выполняет шаг исследования"""
        self.log("INFO", "RESEARCHER", f"--- {name} ---")
        try:
            await fn()
        except Exception as e:
            self.log("ERROR", "RESEARCHER", f"Ошибка в шаге '{name}': {e}")
        await asyncio.sleep(0.2)
    
    async def _check_connection(self):
        """Проверяет подключение к PS"""
        if self.ps.check_connection():
            self.log("SUCCESS", "RESEARCHER", "Plant Simulation подключен")
            self.results.append({
                "method": "COM подключение",
                "code": "Dispatch('Tecnomatix.PlantSimulation.RemoteControl')",
                "success": True,
                "time": 0,
            })
        else:
            self.log("WARN", "RESEARCHER", "Plant Simulation не подключен (демо-режим)")
            self.results.append({
                "method": "COM подключение",
                "code": "Dispatch('Tecnomatix.PlantSimulation.RemoteControl')",
                "success": False,
                "error": "Plant Simulation не запущен",
                "time": 0,
            })
    
    async def _create_test_objects(self):
        """Создаёт тестовые объекты"""
        success, error = self.ps.create_test_objects()
        self.results.append({
            "method": "Создание тестовых объектов",
            "code": ".MaterialFlow.Source.derive(root) + .MaterialFlow.Station.derive(root)",
            "success": success,
            "error": error if not success else None,
            "time": 0,
        })
        if success:
            self.log("SUCCESS", "RESEARCHER", "Тестовые объекты созданы")
        else:
            self.log("ERROR", "RESEARCHER", f"Ошибка: {error}")
    
    async def _test_connection_methods(self):
        """Тестирует все известные методы соединений"""
        methods = self._get_connection_methods()
        
        for method_info in methods:
            name = method_info["name"]
            code = method_info["code"]
            
            success, error, elapsed = self.ps.test_method(code)
            
            result = {
                "method": name,
                "code": code,
                "success": success,
                "error": error if not success else None,
                "time": round(elapsed),
            }
            self.results.append(result)
            
            if success:
                self.known_working.append(result)
                self.log("SUCCESS", "RESEARCHER", f"✅ {name}")
            else:
                self.known_broken.append(result)
                self.log("RESEARCH", "RESEARCHER", f"❌ {name}: {error[:60]}")
            
            await asyncio.sleep(0.1)
    
    async def _introspect_attributes(self):
        """Интроспекция атрибутов объектов"""
        attrs = self.ps.get_object_attributes("TEST_SRC")
        
        self.results.append({
            "method": "Интроспекция Source",
            "code": "putAttributeNamesIntoTable()",
            "success": len(attrs) > 0,
            "error": None if attrs else "Не удалось получить атрибуты",
            "time": 0,
        })
        
        if attrs:
            self.log("SUCCESS", "RESEARCHER", f"Найдено {len(attrs)} атрибутов Source: {', '.join(attrs[:10])}...")
            
            # Ищем интересные атрибуты
            interesting = [a for a in attrs if any(kw in a.lower() for kw in ['connect', 'succ', 'pred', 'link', 'port', 'out', 'in'])]
            if interesting:
                self.log("RESEARCH", "RESEARCHER", f"Интересные атрибуты: {interesting}")
        else:
            self.log("WARN", "RESEARCHER", "Интроспекция не удалась")
    
    async def _test_parameters(self):
        """Тестирует установку параметров"""
        tests = [
            ("interval", 'root.TEST_SRC.interval := 120'),
            ("procTime", 'root.TEST_ST.procTime := 15'),
            ("capacity (Buffer)", 'root.TEST_BUF.capacity := 5'),
        ]
        
        for name, code in tests:
            success, error, elapsed = self.ps.test_method(code)
            self.results.append({
                "method": f"Параметр {name}",
                "code": code,
                "success": success,
                "error": error if not success else None,
                "time": round(elapsed),
            })
            if success:
                self.log("SUCCESS", "RESEARCHER", f"✅ {name} работает")
            else:
                self.log("RESEARCH", "RESEARCHER", f"❌ {name}: {error[:60]}")
            await asyncio.sleep(0.1)
    
    async def _test_object_classes(self):
        """Тестирует имена классов объектов"""
        classes = [
            ("Source", ".MaterialFlow.Source.derive(root, 'CLS_TEST')"),
            ("Station", ".MaterialFlow.Station.derive(root, 'CLS_TEST2')"),
            ("SingleProc (старое)", ".MaterialFlow.SingleProc.derive(root, 'CLS_TEST3')"),
            ("Buffer", ".MaterialFlow.Buffer.derive(root, 'CLS_TEST4')"),
            ("Drain", ".MaterialFlow.Drain.derive(root, 'CLS_TEST5')"),
            ("Line", ".MaterialFlow.Line.derive(root, 'CLS_TEST6')"),
        ]
        
        for name, code in classes:
            success, error, elapsed = self.ps.test_method(code)
            self.results.append({
                "method": f"Класс {name}",
                "code": code,
                "success": success,
                "error": error if not success else None,
                "time": round(elapsed),
            })
            if success:
                self.log("SUCCESS", "RESEARCHER", f"✅ Класс {name} существует")
            else:
                self.log("RESEARCH", "RESEARCHER", f"❌ Класс {name}: {error[:60]}")
            await asyncio.sleep(0.1)
    
    async def _experimental_methods(self):
        """Экспериментальные методы — пробуем нестандартные подходы"""
        experiments = [
            ("xPos/yPos размещение", """
root.TEST_SRC.xPos := 100
root.TEST_SRC.yPos := 200
root.TEST_ST.xPos := 200
root.TEST_ST.yPos := 200
"""),
            ("Connector.derive (2 args)", '.MaterialFlow.Connector.derive(root, "CONN_TEST")'),
            ("connect через root", 'root.connect(root.TEST_SRC, root.TEST_ST)'),
            ("dragTo метод", 'root.TEST_SRC.dragTo(root.TEST_ST)'),
            ("link метод", 'root.TEST_SRC.link(root.TEST_ST)'),
            ("bindTo метод", 'root.TEST_SRC.bindTo(root.TEST_ST)'),
            ("attach метод", 'root.TEST_SRC.attach(root.TEST_ST)'),
            ("outputPort", 'root.TEST_SRC.outputPort := root.TEST_ST'),
            ("outConnector", 'root.TEST_SRC.outConnector := root.TEST_ST'),
        ]
        
        for name, code in experiments:
            success, error, elapsed = self.ps.test_method(code)
            self.results.append({
                "method": f"[EXP] {name}",
                "code": code.strip(),
                "success": success,
                "error": error if not success else None,
                "time": round(elapsed),
            })
            if success:
                self.log("SUCCESS", "RESEARCHER", f"✅ [EXP] {name} — РАБОТАЕТ!")
            else:
                self.log("RESEARCH", "RESEARCHER", f"❌ [EXP] {name}: {error[:60]}")
            await asyncio.sleep(0.1)
    
    async def _cleanup(self):
        """Очистка тестовых объектов"""
        success, error = self.ps.cleanup_test_objects()
        if success:
            self.log("INFO", "RESEARCHER", "Тестовые объекты удалены")
    
    def _get_connection_methods(self) -> list[dict]:
        """Все известные методы создания соединений"""
        return [
            {
                "name": "succ := (read-only)",
                "code": "root.TEST_SRC.succ := root.TEST_ST",
            },
            {
                "name": "succ(1) := (indexed)",
                "code": "root.TEST_SRC.succ(1) := root.TEST_ST",
            },
            {
                "name": "Connector.derive (4 args)",
                "code": '.MaterialFlow.Connector.derive(root, "C1", root.TEST_SRC, root.TEST_ST)',
            },
            {
                "name": "Connector.derive (strings)",
                "code": '.MaterialFlow.Connector.derive(root, "C1", "TEST_SRC", "TEST_ST")',
            },
            {
                "name": "Connector + startpoint",
                "code": """
var c : object
c := .MaterialFlow.Connector.derive(root, "C2")
c.startpoint := root.TEST_SRC
c.endpoint := root.TEST_ST
""",
            },
            {
                "name": "Connector + setFrom/setTo",
                "code": """
var c : object
c := .MaterialFlow.Connector.derive(root, "C3")
c.setFrom(root.TEST_SRC)
c.setTo(root.TEST_ST)
""",
            },
            {
                "name": "Connector + fromObject/toObject",
                "code": """
var c : object
c := .MaterialFlow.Connector.derive(root, "C4")
c.fromObject := root.TEST_SRC
c.toObject := root.TEST_ST
""",
            },
            {
                "name": "Connector + start/end",
                "code": """
var c : object
c := .MaterialFlow.Connector.derive(root, "C5")
c.start := root.TEST_SRC
c.end := root.TEST_ST
""",
            },
            {
                "name": "Connector + pred/succ",
                "code": """
var c : object
c := .MaterialFlow.Connector.derive(root, "C6")
c.pred := root.TEST_SRC
c.succ := root.TEST_ST
""",
            },
            {
                "name": "connect() метод",
                "code": "root.TEST_SRC.connect(root.TEST_ST)",
            },
            {
                "name": "connectTo() метод",
                "code": "root.TEST_SRC.connectTo(root.TEST_ST)",
            },
            {
                "name": "addSucc() метод",
                "code": "root.TEST_SRC.addSucc(root.TEST_ST)",
            },
            {
                "name": "insertSucc() метод",
                "code": "root.TEST_SRC.insertSucc(1, root.TEST_ST)",
            },
            {
                "name": "setSucc() метод",
                "code": "root.TEST_SRC.setSucc(1, root.TEST_ST)",
            },
            {
                "name": "succConnector()",
                "code": "root.TEST_SRC.succConnector(1, root.TEST_ST)",
            },
            {
                "name": "setAttribute()",
                "code": 'root.TEST_SRC.setAttribute("succ", root.TEST_ST)',
            },
        ]
    
    def _get_extra_connection_methods(self) -> list[dict]:
        """Дополнительные экспериментальные методы"""
        return [
            {
                "name": "Connector.derive (3 args, no name)",
                "code": ".MaterialFlow.Connector.derive(root, root.TEST_SRC, root.TEST_ST)",
            },
            {
                "name": "Connector.derive (container only)",
                "code": '.MaterialFlow.Connector.derive(root)',
            },
            {
                "name": "moveTo + auto-connect",
                "code": """
root.TEST_SRC.xPos := 100
root.TEST_SRC.yPos := 200
root.TEST_ST.xPos := 138
root.TEST_ST.yPos := 200
""",
            },
            {
                "name": "connectorList",
                "code": "root.TEST_SRC.connectorList",
            },
            {
                "name": "connections",
                "code": "root.TEST_SRC.connections",
            },
            {
                "name": "ports",
                "code": "root.TEST_SRC.ports",
            },
            {
                "name": "exitStrategy",
                "code": "root.TEST_SRC.exitStrategy",
            },
        ]
