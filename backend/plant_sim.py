"""
COM-интерфейс к Siemens Plant Simulation 2404

Подтверждённые рабочие факты:
- derive() — создание объектов (НЕ create!)
- Station — класс станции (НЕ SingleProc!)
- setName() — переименование (НЕ .name := !)
- deleteObject — удаление
- succ — только для чтения!
- Строки — только двойные кавычки
- return — только внутри методов
"""

import sys
import time
import traceback
from pathlib import Path
from typing import Optional

# COM доступен только на Windows
try:
    import pythoncom
    import win32com.client
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
            # В демо-режиме симулируем выполнение
            return self._demo_execute(code)
        
        try:
            self.app.ExecuteSimTalk(code)
            return True, ""
        except Exception as e:
            error_msg = str(e)
            # Извлекаем сообщение об ошибке из COM-исключения
            if isinstance(e, tuple) and len(e) > 2:
                error_msg = str(e[2]) if len(e) > 2 else str(e)
            return False, error_msg
    
    def save_model(self, path: str) -> tuple[bool, str]:
        """Сохраняет модель"""
        if self._demo_mode:
            return True, "demo"
        try:
            # Создаём директорию если нужно
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
        time.sleep(0.1)  # Имитация задержки
        
        # Определяем тип операции
        if "derive" in code and "EventController" in code:
            return True, ""
        elif "derive" in code:
            return True, ""
        elif "setName" in code:
            return True, ""
        elif ":=" in code and "root." in code:
            # Установка параметров
            if "succ" in code:
                return False, "cannot assign to left hand side"
            return True, ""
        elif "connect" in code.lower():
            return False, "Unknown identifier 'connect'"
        elif "Connector.derive" in code:
            return False, "Wrong number of parameters"
        
        return True, ""
    
    # ─── Методы для исследователя ─────────────────────────────────────
    
    def test_method(self, code: str) -> tuple[bool, str, float]:
        """Тестирует метод и возвращает (успех, ошибка, время_ms)"""
        start = time.time()
        success, error = self.execute(code)
        elapsed = (time.time() - start) * 1000
        return success, error, elapsed
    
    def create_test_objects(self) -> tuple[bool, str]:
        """Создаёт тестовые объекты для экспериментов"""
        code = """
var pa : object
pa := .MaterialFlow.Source.derive(root)
pa.setName("TEST_SRC")

var pb : object
pb := .MaterialFlow.Station.derive(root)
pb.setName("TEST_ST")
"""
        return self.execute(code)
    
    def cleanup_test_objects(self) -> tuple[bool, str]:
        """Удаляет тестовые объекты"""
        code = """
root.TEST_SRC.deleteObject
root.TEST_ST.deleteObject
"""
        return self.execute(code)
    
    def get_object_attributes(self, obj_path: str) -> list[str]:
        """Получает список атрибутов объекта (интроспекция)"""
        if self._demo_mode:
            return ["name", "class", "interval", "procTime", "capacity", "succ", "pred"]
        
        try:
            # Создаём DataTable для хранения имён атрибутов
            self.execute(f"""
var t : object
t := .InformationFlow.DataTable.derive(root, "ATTRS_TABLE")
root.{obj_path.split('.')[-1]}.putAttributeNamesIntoTable(root.ATTRS_TABLE)
""")
            
            # Читаем таблицу
            attrs = []
            i = 1
            while i < 1000:
                try:
                    val = self.app.GetTableCell("root.ATTRS_TABLE", i, 1)
                    if val:
                        attrs.append(str(val))
                    else:
                        break
                except Exception:
                    break
                i += 1
            
            # Удаляем таблицу
            self.execute("root.ATTRS_TABLE.deleteObject")
            return attrs
            
        except Exception:
            return []
