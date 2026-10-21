"""
COM-интерфейс к Siemens Plant Simulation 2404
Согласно ТЗ v1.0

Подтверждённые рабочие методы API:
- createObject(f, x, y) — создание объектов
- Connector.connect(obj1, obj2) — создание связей (класс-метод!)
- setName() — переименование
- .Models.Model — фрейм по умолчанию
"""

import sys
import time
from pathlib import Path
from typing import Optional

# COM доступен только на Windows
try:
    import pythoncom
    import win32com.client
    import psutil
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False


class PlantSimConnection:
    """COM-интерфейс к Plant Simulation 2404"""
    
    def __init__(self):
        self.app = None
        self.connected = False
        self._demo_mode = not COM_AVAILABLE
    
    def check_connection(self) -> bool:
        """Проверяет доступность Plant Simulation"""
        if self._demo_mode:
            return False
        
        try:
            # Убиваем zombie-процессы
            self._kill_zombie_processes()
            
            pythoncom.CoInitialize()
            self.app = win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl")
            self.app.SetNoMessageBox(True)
            try:
                self.app.SetSuppressOpenGL(True)
            except Exception:
                pass
            self.connected = True
            return True
        except Exception as e:
            print(f"[PlantSim] Не удалось подключиться: {e}")
            self.connected = False
            return False
    
    def _kill_zombie_processes(self):
        """Убивает zombie-процессы Plant Simulation (согласно ТЗ US-3)"""
        if not COM_AVAILABLE:
            return
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and 'plantsimulation' in proc.info['name'].lower():
                    print(f"[PlantSim] Zombie-процесс обнаружен: PID {proc.info['pid']}")
                    proc.kill()
                    time.sleep(1)
        except Exception as e:
            print(f"[PlantSim] Ошибка проверки процессов: {e}")
    
    def new_model(self) -> tuple[bool, str]:
        """Создаёт новую модель"""
        if self._demo_mode:
            return True, "demo"
        try:
            self.app.NewModel()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def execute(self, code: str) -> tuple[bool, str]:
        """Выполняет SimTalk код"""
        if self._demo_mode:
            return self._demo_execute(code)
        
        try:
            self.app.ExecuteSimTalk(code)
            return True, ""
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, tuple) and len(e) > 2:
                error_msg = str(e[2]) if len(e) > 2 else str(e)
            return False, error_msg
    
    def save_model(self, path: str) -> tuple[bool, str]:
        """Сохраняет модель"""
        if self._demo_mode:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).touch()
            return True, "demo"
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self.app.SaveModel(path)
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def close_model(self) -> tuple[bool, str]:
        """Закрывает модель"""
        if self._demo_mode:
            return True, "demo"
        try:
            self.app.CloseModel()
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _demo_execute(self, code: str) -> tuple[bool, str]:
        """Демо-режим: симулирует выполнение"""
        time.sleep(0.05)
        
        # Проверяем правильность синтаксиса
        if "createObject" in code:
            return True, ""
        elif "Connector.connect" in code:
            return True, ""
        elif "setName" in code:
            return True, ""
        elif ":=" in code and ".Models.Model" in code:
            return True, ""
        elif "SingleProc" in code or "ParallelProc" in code:
            return False, "Unknown identifier 'SingleProc'"
        elif ".succ :=" in code:
            return False, "cannot assign to left hand side"
        
        return True, ""
    
    # ─── Методы для исследователя ─────────────────────────────────────
    
    def test_method(self, code: str) -> tuple[bool, str, float]:
        """Тестирует метод и возвращает (успех, ошибка, время_ms)"""
        start = time.time()
        success, error = self.execute(code)
        elapsed = (time.time() - start) * 1000
        return success, error, elapsed
    
    def create_test_objects(self) -> tuple[bool, str]:
        """Создаёт тестовые объекты для экспериментов (по ТЗ)"""
        code = """
var f : object
f := .Models.Model

var pa : object
pa := .MaterialFlow.Source.createObject(f, 100, 100)
pa.setName("TEST_SRC")

var pb : object
pb := .MaterialFlow.Station.createObject(f, 220, 100)
pb.setName("TEST_ST")
"""
        return self.execute(code)
    
    def cleanup_test_objects(self) -> tuple[bool, str]:
        """Удаляет тестовые объекты"""
        code = """
var f : object
f := .Models.Model
f.TEST_SRC.deleteObject
f.TEST_ST.deleteObject
"""
        return self.execute(code)
    
    def get_object_attributes(self, obj_path: str) -> list[str]:
        """Получает список атрибутов объекта (интроспекция)"""
        if self._demo_mode:
            return ["name", "class", "interval", "procTime", "capacity"]
        
        try:
            self.execute(f"""
var f : object
f := .Models.Model
var t : object
t := .InformationFlow.DataTable.createObject(f, "ATTRS_TABLE")
f.{obj_path}.putAttributeNamesIntoTable(t)
""")
            
            attrs = []
            i = 1
            while i < 1000:
                try:
                    val = self.app.GetTableCell(f".Models.Model.ATTRS_TABLE", i, 1)
                    if val:
                        attrs.append(str(val))
                    else:
                        break
                except Exception:
                    break
                i += 1
            
            self.execute(".Models.Model.ATTRS_TABLE.deleteObject")
            return attrs
            
        except Exception:
            return []
