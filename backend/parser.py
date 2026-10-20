"""
Fallback regex-парсер описания производственной линии
Работает когда Ollama недоступна
"""

import re
from typing import Optional


def fallback_parse(description: str) -> dict:
    """
    Парсит текстовое описание в JSON-спецификацию.
    
    Поддерживает:
    - Источник/Source/Генератор
    - Станция/Station/Обработка
    - Накопитель/Буфер/Buffer
    - Сход/Drain/Выход
    - Параметры: интервал, время обработки, ёмкость
    """
    objects = []
    connections = []
    desc_lower = description.lower()
    
    # ─── Объекты ──────────────────────────────────────────────────────
    
    # Источник
    if re.search(r'источник|source|генератор|генер', desc_lower):
        obj = {"name": "SRC_1", "class": "Source", "params": {}}
        
        # Ищем интервал
        interval = _extract_number(description, r'интервал[а-я]*\s*(?:в\s*)?(\d+)\s*(?:мин|сек|s|min)?')
        if interval:
            # Определяем единицы
            if re.search(r'мин|min', description[interval[1]:interval[1]+20], re.I):
                obj["params"]["interval"] = interval[0] * 60  # минуты → секунды
            else:
                obj["params"]["interval"] = interval[0]
        else:
            # Пробуем "каждые N секунд/минут"
            every = _extract_number(description, r'кажд[а-я]*\s*(\d+)\s*(?:мин|сек|s|min)?')
            if every:
                if re.search(r'мин|min', description[every[1]:every[1]+20], re.I):
                    obj["params"]["interval"] = every[0] * 60
                else:
                    obj["params"]["interval"] = every[0]
        
        objects.append(obj)
    
    # Станция
    station_matches = list(re.finditer(r'станци[яий]|station|обработк[а-я]*|пост', desc_lower))
    for i, match in enumerate(station_matches):
        name = f"ST_{i+1}" if i > 0 else "ST_1"
        obj = {"name": name, "class": "Station", "params": {}}
        
        # Время обработки
        proc = _extract_number_near(description, r'(?:обработк[а-я]*|время|procTime)\s*(?:[а-я]*\s*)?(\d+)', match.start())
        if proc:
            if re.search(r'мин|min', description[proc[1]:proc[1]+20], re.I):
                obj["params"]["procTime"] = proc[0] * 60
            else:
                obj["params"]["procTime"] = proc[0]
        else:
            # Ищем просто число рядом с "станция"
            nearby = _extract_number_near(description, r'(\d+)\s*(?:сек|секунд|s)?', match.start())
            if nearby and nearby[0] < 1000:
                obj["params"]["procTime"] = nearby[0]
        
        objects.append(obj)
    
    # Буфер / Накопитель
    buffer_matches = list(re.finditer(r'накопител[ь-я]|буфер|buffer|емкост', desc_lower))
    for i, match in enumerate(buffer_matches):
        name = f"BUF_{i+1}" if i > 0 else "BUF_1"
        obj = {"name": name, "class": "Buffer", "params": {}}
        
        # Ёмкость
        cap = _extract_number_near(description, r'(?:на\s*)?(\d+)\s*(?:мест|шт|штук)?', match.start())
        if cap and cap[0] < 10000:
            obj["params"]["capacity"] = cap[0]
        
        objects.append(obj)
    
    # Сход / Выход
    if re.search(r'сход|drain|выход|вых[од]*|приёмник', desc_lower):
        objects.append({"name": "DRN_1", "class": "Drain", "params": {}})
    
    # ─── Соединения (последовательные) ────────────────────────────────
    
    for i in range(len(objects) - 1):
        connections.append([objects[i]["name"], objects[i + 1]["name"]])
    
    return {"objects": objects, "connections": connections}


def _extract_number(text: str, pattern: str) -> Optional[tuple[int, int]]:
    """Извлекает число по паттерну. Возвращает (число, позиция) или None."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return (int(match.group(1)), match.start(1))
        except (ValueError, IndexError):
            pass
    return None


def _extract_number_near(text: str, pattern: str, near_pos: int, window: int = 80) -> Optional[tuple[int, int]]:
    """Извлекает число рядом с указанной позицией."""
    start = max(0, near_pos - 10)
    end = min(len(text), near_pos + window)
    segment = text[start:end]
    
    match = re.search(pattern, segment, re.IGNORECASE)
    if match:
        try:
            return (int(match.group(1)), start + match.start(1))
        except (ValueError, IndexError):
            pass
    return None


# ─── Тест ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        "Источник заготовок с интервалом 3 минуты, станция обработки 20 секунд, накопитель на 10 мест, сход",
        "Генератор каждые 60 секунд, две станции по 15 секунд, накопитель 5, выход",
        "Source interval 120, Station procTime 30, Buffer capacity 20, Drain",
        "Линия: источник 180 сек, станция 20, буфер 10, сход",
    ]
    
    for test in tests:
        print(f"\nОписание: {test}")
        result = fallback_parse(test)
        print(f"Объекты: {result['objects']}")
        print(f"Соединения: {result['connections']}")
