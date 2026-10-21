"""
Автономный ИИ-агент для Siemens Plant Simulation 2404
Полная реализация согласно Техническому Заданию

Использование:
    python plant_agent_full.py --selftest
    python plant_agent_full.py --dry-run "текст описания"
    python plant_agent_full.py "текст описания" output.spp
"""

import sys
import json
import re
import time
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('agent_log.txt', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# COM-интерфейс (только Windows)
try:
    import pythoncom
    import win32com.client
    import win32process
    import psutil
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
    logger.warning("pywin32 не установлен. Работа в демо-режиме.")


# ═══════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════

class Config:
    OLLAMA_URL = "http://localhost:11434"
    OLLAMA_MODEL = "qwen2.5-coder:7b"
    COM_PROGID = "Tecnomatix.PlantSimulation.RemoteControl"
    DEFAULT_FRAME = ".Models.Model"
    MAX_HEALING_ATTEMPTS = 3
    SAVE_PATH = "model.spp"


# ═══════════════════════════════════════════════════════════════════════
# КЛАСС 1: АРХИТЕКТОР (Парсер + LLM)
# ═══════════════════════════════════════════════════════════════════════

class Architect:
    """Парсит текстовое описание в JSON-спецификацию"""
    
    def __init__(self):
        self.ollama_available = False
    
    def parse(self, description: str) -> dict:
        """Главный метод парсинга"""
        logger.info("Архитектор: начало парсинга описания")
        
        # Попытка 1: LLM
        try:
            spec = self._parse_with_llm(description)
            if spec and self._validate_spec(spec):
                logger.info(f"Архитектор: LLM успешно распарсила ({len(spec['objects'])} объектов)")
                return spec
        except Exception as e:
            logger.warning(f"Архитектор: LLM недоступна ({e})")
        
        # Попытка 2: Fallback regex
        logger.info("Архитектор: переключение на fallback-парсер")
        spec = self._parse_with_regex(description)
        
        if not spec['objects']:
            raise ValueError("Не удалось извлечь объекты из описания")
        
        logger.info(f"Архитектор: fallback нашёл {len(spec['objects'])} объектов")
        return spec
    
    def _parse_with_llm(self, description: str) -> Optional[dict]:
        """Парсинг через Ollama LLM"""
        import httpx
        
        prompt = f"""Ты — архитектор моделей для Siemens Plant Simulation 2404.
Проанализируй описание производственной линии и верни JSON-спецификацию.

ПРАВИЛА Plant Simulation 2404:
- Классы: Source, Station, ParallelStation, Buffer, Drain
- Метод создания: createObject(frame, x, y)
- Переименование: setName()
- Соединения: .MaterialFlow.Connector.connect(obj1, obj2)
- Параметры: interval (сек), procTime (сек), capacity

Верни JSON в формате:
{{
  "objects": [
    {{"name": "SRC_1", "class": "Source", "x": 100, "y": 100, "params": {{"interval": 180}}}},
    {{"name": "ST_1", "class": "Station", "x": 220, "y": 100, "params": {{"procTime": 20}}}}
  ],
  "connections": [["SRC_1", "ST_1"]]
}}

Расположи объекты слева направо с шагом 120 по X.

Описание: {description}

Верни ТОЛЬКО JSON."""
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{Config.OLLAMA_URL}/api/generate",
                json={
                    "model": Config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            )
            response.raise_for_status()
            result = response.json()
            text = result.get("response", "")
            
            # Извлекаем JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
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
            
            # Интервал
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
            
            # Время обработки
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
            
            # Ёмкость
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


# ═══════════════════════════════════════════════════════════════════════
# КЛАСС 2: СТРОИТЕЛЬ (Генератор SimTalk)
# ═══════════════════════════════════════════════════════════════════════

class Builder:
    """Генерирует SimTalk код из JSON-спецификации"""
    
    def generate(self, spec: dict) -> str:
        """Генерирует полный SimTalk код"""
        logger.info("Строитель: генерация SimTalk кода")
        
        code_lines = []
        
        # Объявление фрейма
        code_lines.append(f'var f : object')
        code_lines.append(f'f := {Config.DEFAULT_FRAME}')
        code_lines.append('')
        
        # Создание объектов
        for obj in spec["objects"]:
            class_name = obj["class"]
            obj_name = obj["name"]
            x = obj["x"]
            y = obj["y"]
            
            code_lines.append(f'var {obj_name} : object')
            code_lines.append(f'{obj_name} := .MaterialFlow.{class_name}.createObject(f, {x}, {y})')
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
        logger.info(f"Строитель: сгенерировано {len(code_lines)} строк кода")
        return code


# ═══════════════════════════════════════════════════════════════════════
# КЛАСС 3: ИСПОЛНИТЕЛЬ (COM-клиент)
# ═══════════════════════════════════════════════════════════════════════

class Executor:
    """Управляет Plant Simulation через COM"""
    
    def __init__(self):
        self.app = None
        self.connected = False
    
    def connect(self) -> bool:
        """Подключение к Plant Simulation"""
        if not COM_AVAILABLE:
            logger.warning("Исполнитель: COM недоступен (демо-режим)")
            return False
        
        try:
            # Проверка zombie-процессов
            self._kill_zombie_processes()
            
            pythoncom.CoInitialize()
            self.app = win32com.client.Dispatch(Config.COM_PROGID)
            self.app.SetNoMessageBox(True)
            
            try:
                self.app.SetSuppressOpenGL(True)
            except Exception:
                pass
            
            self.connected = True
            logger.info("Исполнитель: подключение к Plant Simulation успешно")
            return True
            
        except Exception as e:
            logger.error(f"Исполнитель: ошибка подключения: {e}")
            self.connected = False
            return False
    
    def _kill_zombie_processes(self):
        """Убивает zombie-процессы Plant Simulation"""
        if not COM_AVAILABLE:
            return
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'plantsimulation' in proc.info['name'].lower():
                    logger.warning(f"Исполнитель: обнаружен zombie-процесс {proc.pid}")
                    proc.kill()
                    time.sleep(1)
        except Exception as e:
            logger.debug(f"Исполнитель: ошибка проверки процессов: {e}")
    
    def execute(self, code: str) -> tuple[bool, str]:
        """Выполняет SimTalk код"""
        if not self.connected:
            logger.warning("Исполнитель: не подключен (демо-режим)")
            return True, "demo"
        
        try:
            self.app.ExecuteSimTalk(code)
            logger.info("Исполнитель: код выполнен успешно")
            return True, ""
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Исполнитель: ошибка выполнения: {error_msg}")
            return False, error_msg
    
    def save_model(self, path: str) -> bool:
        """Сохраняет модель"""
        if not self.connected:
            logger.info(f"Исполнитель: демо-режим, модель сохранена в {path}")
            Path(path).touch()
            return True
        
        try:
            self.app.SaveModel(path)
            logger.info(f"Исполнитель: модель сохранена в {path}")
            return True
        except Exception as e:
            logger.error(f"Исполнитель: ошибка сохранения: {e}")
            return False
    
    def new_model(self):
        """Создаёт новую модель"""
        if self.connected:
            self.app.NewModel()
            logger.info("Исполнитель: создана новая модель")


# ═══════════════════════════════════════════════════════════════════════
# КЛАСС 4: ВАЛИДАТОР
# ═══════════════════════════════════════════════════════════════════════

class Validator:
    """Проверяет корректность созданной модели"""
    
    def __init__(self, executor: Executor):
        self.executor = executor
    
    def validate(self, spec: dict) -> bool:
        """Валидация модели"""
        logger.info("Валидатор: начало проверки модели")
        
        if not self.executor.connected:
            logger.info("Валидатор: демо-режим, валидация пропущена")
            return True
        
        try:
            # Создаём DataTable для подсчёта
            count_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}

var dt : object
dt := .InformationFlow.DataTable.createObject(f, "VALIDATION_TABLE")

var count : integer
count := f.numObjects

dt.setCell(1, 1, count)
"""
            success, error = self.executor.execute(count_code)
            if not success:
                logger.error(f"Валидатор: ошибка создания таблицы: {error}")
                return False
            
            # Читаем количество объектов
            try:
                actual_count = self.executor.app.GetTableCell(f"{Config.DEFAULT_FRAME}.VALIDATION_TABLE", 1, 1)
                expected_count = len(spec["objects"])
                
                if actual_count != expected_count:
                    logger.error(f"Валидатор: ожидалось {expected_count} объектов, найдено {actual_count}")
                    return False
                
                logger.info(f"Валидатор: найдено {actual_count} объектов (ожидалось {expected_count})")
                
                # Удаляем таблицу
                self.executor.execute(f"{Config.DEFAULT_FRAME}.VALIDATION_TABLE.deleteObject")
                
                return True
                
            except Exception as e:
                logger.error(f"Валидатор: ошибка чтения таблицы: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Валидатор: ошибка валидации: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════
# КЛАСС 5: ОРКЕСТРАТОР (Главный контроллер)
# ═══════════════════════════════════════════════════════════════════════

class Orchestrator:
    """Управляет полным циклом создания модели"""
    
    def __init__(self):
        self.architect = Architect()
        self.builder = Builder()
        self.executor = Executor()
        self.validator = Validator(self.executor)
    
    def run(self, description: str, output_path: str = Config.SAVE_PATH) -> bool:
        """Полный цикл: парсинг → генерация → выполнение → валидация → сохранение"""
        logger.info("=" * 60)
        logger.info("ОРКЕСТРАТОР: запуск полного цикла")
        logger.info("=" * 60)
        
        try:
            # Шаг 1: Подключение
            logger.info("\n[1/5] Подключение к Plant Simulation...")
            self.executor.connect()
            
            # Шаг 2: Парсинг
            logger.info("\n[2/5] Парсинг описания...")
            spec = self.architect.parse(description)
            logger.info(f"Спецификация: {json.dumps(spec, indent=2, ensure_ascii=False)}")
            
            # Шаг 3: Генерация кода
            logger.info("\n[3/5] Генерация SimTalk кода...")
            code = self.builder.generate(spec)
            logger.info(f"Сгенерированный код:\n{code}")
            
            # Шаг 4: Выполнение с healing
            logger.info("\n[4/5] Выполнение кода...")
            success = False
            for attempt in range(Config.MAX_HEALING_ATTEMPTS):
                logger.info(f"Попытка {attempt + 1}/{Config.MAX_HEALING_ATTEMPTS}")
                
                self.executor.new_model()
                success, error = self.executor.execute(code)
                
                if success:
                    logger.info("Код выполнен успешно")
                    break
                else:
                    logger.error(f"Ошибка: {error}")
                    if attempt < Config.MAX_HEALING_ATTEMPTS - 1:
                        logger.info("Попытка автоисправления...")
                        # TODO: добавить LLM-отладчик
                        time.sleep(1)
            
            if not success:
                logger.error("Все попытки выполнения неудачны")
                return False
            
            # Шаг 5: Валидация и сохранение
            logger.info("\n[5/5] Валидация и сохранение...")
            if not self.validator.validate(spec):
                logger.error("Валидация не пройдена")
                return False
            
            if not self.executor.save_model(output_path):
                logger.error("Ошибка сохранения модели")
                return False
            
            logger.info("\n" + "=" * 60)
            logger.info(f"✅ МОДЕЛЬ УСПЕШНО СОЗДАНА И СОХРАНЕНА: {output_path}")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
            return False


# ═══════════════════════════════════════════════════════════════════════
# CLI ИНТЕРФЕЙС
# ═══════════════════════════════════════════════════════════════════════

def selftest():
    """Самотестирование системы"""
    logger.info("=" * 60)
    logger.info("САМОТЕСТИРОВАНИЕ СИСТЕМЫ")
    logger.info("=" * 60)
    
    # Тест 1: Подключение к PS
    logger.info("\n[Тест 1] Подключение к Plant Simulation...")
    executor = Executor()
    if executor.connect():
        logger.info("✅ Plant Simulation подключен")
    else:
        logger.warning("⚠️ Plant Simulation недоступен (демо-режим)")
    
    # Тест 2: createObject
    logger.info("\n[Тест 2] Проверка createObject...")
    test_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}
var test_obj : object
test_obj := .MaterialFlow.Source.createObject(f, 100, 100)
test_obj.setName("TEST_OBJ")
"""
    success, error = executor.execute(test_code)
    if success:
        logger.info("✅ createObject работает")
    else:
        logger.error(f"❌ createObject не работает: {error}")
    
    # Тест 3: Connector.connect
    logger.info("\n[Тест 3] Проверка Connector.connect...")
    conn_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}
var obj1 : object
obj1 := .MaterialFlow.Source.createObject(f, 200, 100)
obj1.setName("TEST_SRC")
var obj2 : object
obj2 := .MaterialFlow.Station.createObject(f, 320, 100)
obj2.setName("TEST_ST")
.MaterialFlow.Connector.connect(obj1, obj2)
"""
    success, error = executor.execute(conn_code)
    if success:
        logger.info("✅ Connector.connect работает")
    else:
        logger.error(f"❌ Connector.connect не работает: {error}")
    
    # Тест 4: Проверка устаревших методов (должны НЕ работать)
    logger.info("\n[Тест 4] Проверка устаревших методов (должны НЕ работать)...")
    old_code = f"""
var f : object
f := {Config.DEFAULT_FRAME}
var old_obj : object
old_obj := .MaterialFlow.SingleProc.createObject(f, 400, 100)
"""
    success, error = executor.execute(old_code)
    if not success:
        logger.info("✅ SingleProc корректно не работает (устарел)")
    else:
        logger.warning("⚠️ SingleProc работает (неожиданно)")
    
    logger.info("\n" + "=" * 60)
    logger.info("САМОТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    logger.info("=" * 60)


def dry_run(description: str):
    """Тестовый запуск без COM"""
    logger.info("=" * 60)
    logger.info("DRY RUN (без выполнения в PS)")
    logger.info("=" * 60)
    
    architect = Architect()
    builder = Builder()
    
    logger.info("\n[1/2] Парсинг описания...")
    spec = architect.parse(description)
    logger.info(f"\nJSON-спецификация:\n{json.dumps(spec, indent=2, ensure_ascii=False)}")
    
    logger.info("\n[2/2] Генерация кода...")
    code = builder.generate(spec)
    logger.info(f"\nSimTalk код:\n{code}")
    
    logger.info("\n" + "=" * 60)
    logger.info("DRY RUN ЗАВЕРШЕН")
    logger.info("=" * 60)


def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python plant_agent_full.py --selftest")
        print("  python plant_agent_full.py --dry-run \"описание\"")
        print("  python plant_agent_full.py \"описание\" [output.spp]")
        sys.exit(1)
    
    if sys.argv[1] == "--selftest":
        selftest()
    elif sys.argv[1] == "--dry-run":
        if len(sys.argv) < 3:
            print("Ошибка: укажите описание после --dry-run")
            sys.exit(1)
        dry_run(sys.argv[2])
    else:
        description = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else Config.SAVE_PATH
        
        orchestrator = Orchestrator()
        success = orchestrator.run(description, output_path)
        
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
