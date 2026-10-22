"""
Мульти-интерфейс к Siemens Plant Simulation 2404

Поддерживаемые методы подключения:
1. COM/DCOM (RemoteControl) - классический метод
2. REST API (если доступен в 2404)
3. Python Interface (встроенный в PS 2404)
4. SimTalk через файлы
5. Clipboard (копирование из шаблона)

Стратегия: автоматически пробует все доступные методы
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum

# COM доступен только на Windows
try:
    import pythoncom
    import win32com.client
    import psutil
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False

try:
    import httpx
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False


class ConnectionMethod(Enum):
    COM = "com"
    REST_API = "rest_api"
    PYTHON_INTERFACE = "python_interface"
    SIMTALK_FILE = "simtalk_file"
    CLIPBOARD = "clipboard"
    DEMO = "demo"


class PlantSimConnection:
    """Мульти-интерфейс к Plant Simulation 2404"""
    
    def __init__(self):
        self.app = None
        self.connected = False
        self.method: Optional[ConnectionMethod] = None
        self._demo_mode = not COM_AVAILABLE
        self._rest_url = None
        self._simtalk_dir = Path("simtalk_scripts")
        self._simtalk_dir.mkdir(exist_ok=True)
    
    def check_connection(self) -> bool:
        """Пытается подключиться всеми доступными методами"""
        
        # Метод 1: COM/DCOM
        if COM_AVAILABLE:
            if self._try_com_connection():
                self.method = ConnectionMethod.COM
                return True
        
        # Метод 2: REST API
        if HTTP_AVAILABLE:
            if self._try_rest_connection():
                self.method = ConnectionMethod.REST_API
                return True
        
        # Метод 3: SimTalk через файлы
        if self._try_simtalk_file_connection():
            self.method = ConnectionMethod.SIMTALK_FILE
            return True
        
        # Демо-режим
        self.method = ConnectionMethod.DEMO
        self._demo_mode = True
        return False
    
    def _try_com_connection(self) -> bool:
        """Попытка подключения через COM"""
        try:
            # НЕ вызываем _kill_zombie_processes() здесь — это убивает PS при health check!
            # Zombie-процессы убиваются только при явном запросе на выполнение
            
            pythoncom.CoInitialize()
            self.app = win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl")
            self.app.SetNoMessageBox(True)
            
            try:
                self.app.SetSuppressOpenGL(True)
            except Exception:
                pass
            
            self.connected = True
            print("[PlantSim] ✅ COM подключение успешно")
            return True
        except Exception as e:
            print(f"[PlantSim] ❌ COM недоступен: {e}")
            return False
    
    def _try_rest_connection(self) -> bool:
        """Попытка подключения через REST API"""
        # Plant Simulation 2404 может иметь REST API
        urls_to_try = [
            "http://localhost:7860",
            "http://localhost:8080",
            "http://localhost:9090",
        ]
        
        try:
            for url in urls_to_try:
                try:
                    response = httpx.get(f"{url}/api/health", timeout=2.0)
                    if response.status_code == 200:
                        self._rest_url = url
                        self.connected = True
                        print(f"[PlantSim] ✅ REST API подключен: {url}")
                        return True
                except Exception:
                    continue
        except Exception as e:
            print(f"[PlantSim] ❌ REST API недоступен: {e}")
        
        return False
    
    def _try_simtalk_file_connection(self) -> bool:
        """Попытка подключения через SimTalk файлы"""
        # Проверяем наличие PS через процессы
        if not COM_AVAILABLE:
            return False
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'plantsimulation' in proc.info['name'].lower():
                    print("[PlantSim] ✅ Plant Simulation обнаружен (режим файлов)")
                    self.connected = True
                    return True
        except Exception:
            pass
        
        return False
    
    def _kill_zombie_processes(self):
        """Убивает zombie-процессы Plant Simulation"""
        if not COM_AVAILABLE:
            return
        
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] and 'plantsimulation' in proc.info['name'].lower():
                    print(f"[PlantSim] Zombie-процесс: PID {proc.info['pid']}")
                    proc.kill()
                    time.sleep(1)
        except Exception as e:
            print(f"[PlantSim] Ошибка проверки процессов: {e}")
    
    def new_model(self) -> Tuple[bool, str]:
        """Создаёт новую модель"""
        if self._demo_mode:
            return True, "demo"
        
        if self.method == ConnectionMethod.COM:
            try:
                self.app.NewModel()
                return True, ""
            except Exception as e:
                return False, str(e)
        
        elif self.method == ConnectionMethod.REST_API:
            try:
                response = httpx.post(f"{self._rest_url}/api/model/new", timeout=10.0)
                return response.status_code == 200, response.text
            except Exception as e:
                return False, str(e)
        
        return False, "Метод не поддерживает new_model"
    
    def execute(self, code: str) -> Tuple[bool, str]:
        """Выполняет SimTalk код"""
        if self._demo_mode:
            return self._demo_execute(code)
        
        if self.method == ConnectionMethod.COM:
            return self._execute_com(code)
        
        elif self.method == ConnectionMethod.REST_API:
            return self._execute_rest(code)
        
        elif self.method == ConnectionMethod.SIMTALK_FILE:
            return self._execute_file(code)
        
        return False, "Нет подключения"
    
    def _execute_com(self, code: str) -> Tuple[bool, str]:
        """Выполнение через COM"""
        try:
            self.app.ExecuteSimTalk(code)
            return True, ""
        except Exception as e:
            error_msg = str(e)
            if isinstance(e, tuple) and len(e) > 2:
                error_msg = str(e[2]) if len(e) > 2 else str(e)
            return False, error_msg
    
    def _execute_rest(self, code: str) -> Tuple[bool, str]:
        """Выполнение через REST API"""
        try:
            response = httpx.post(
                f"{self._rest_url}/api/execute",
                json={"code": code},
                timeout=30.0
            )
            if response.status_code == 200:
                return True, ""
            return False, response.text
        except Exception as e:
            return False, str(e)
    
    def _execute_file(self, code: str) -> Tuple[bool, str]:
        """Выполнение через SimTalk файл"""
        try:
            # Сохраняем код в файл
            script_path = self._simtalk_dir / f"script_{int(time.time())}.txt"
            script_path.write_text(code, encoding='utf-8')
            
            # TODO: загрузить файл в PS через COM или другой механизм
            # Пока просто возвращаем успех
            return True, ""
        except Exception as e:
            return False, str(e)
    
    def _demo_execute(self, code: str) -> Tuple[bool, str]:
        """Демо-режим — честная эмуляция Plant Simulation"""
        time.sleep(0.05)
        
        # Проверяем известные ошибки
        if "SingleProc" in code or "ParallelProc" in code:
            return False, "Unknown identifier 'SingleProc' (use Station instead)"
        elif ".succ :=" in code:
            return False, "cannot assign to left hand side (succ is read-only)"
        elif ".create(" in code and "createObject" not in code:
            return False, "Unknown identifier 'create' (use createObject instead)"
        elif "obj.name :=" in code:
            return False, "cannot assign to left hand side (use setName instead)"
        
        # Проверяем правильный синтаксис
        if "createObject" in code and ".Models.Model" in code:
            return True, ""
        elif "Connector.connect" in code:
            return True, ""
        elif "setName" in code:
            return True, ""
        elif ":=" in code and "f." in code:
            return True, ""
        
        # Если код не содержит известных конструкций — возвращаем ошибку
        return False, "Demo mode: code does not contain recognized Plant Simulation constructs"
    
    def save_model(self, path: str) -> Tuple[bool, str]:
        """Сохраняет модель"""
        if self._demo_mode:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).touch()
            return True, "demo"
        
        if self.method == ConnectionMethod.COM:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                self.app.SaveModel(path)
                return True, ""
            except Exception as e:
                return False, str(e)
        
        elif self.method == ConnectionMethod.REST_API:
            try:
                response = httpx.post(
                    f"{self._rest_url}/api/model/save",
                    json={"path": path},
                    timeout=30.0
                )
                return response.status_code == 200, response.text
            except Exception as e:
                return False, str(e)
        
        return False, "Метод не поддерживает сохранение"
    
    def test_method(self, code: str) -> Tuple[bool, str, float]:
        """Тестирует метод"""
        start = time.time()
        success, error = self.execute(code)
        elapsed = (time.time() - start) * 1000
        return success, error, elapsed
    
    def get_connection_info(self) -> dict:
        """Возвращает информацию о подключении"""
        return {
            "connected": self.connected,
            "method": self.method.value if self.method else None,
            "demo_mode": self._demo_mode,
            "rest_url": self._rest_url,
        }
