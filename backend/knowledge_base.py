"""
База знаний системы - накопление опыта и решений
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import threading


class KnowledgeBase:
    """База знаний для накопления опыта работы с Plant Simulation"""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    method_name TEXT NOT NULL UNIQUE,
                    code_template TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.0,
                    attempts INTEGER DEFAULT 0,
                    successes INTEGER DEFAULT 0,
                    last_used TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS error_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_message TEXT NOT NULL UNIQUE,
                    solution TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_seen TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS working_solutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_description TEXT NOT NULL,
                    solution_code TEXT NOT NULL,
                    success_count INTEGER DEFAULT 1,
                    last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS object_classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT UNIQUE NOT NULL,
                    create_method TEXT NOT NULL,
                    required_params TEXT,
                    notes TEXT,
                    verified INTEGER DEFAULT 0
                )
            """)
            
            # Инициализация известных фактов
            self._init_known_facts(conn)
            conn.commit()
    
    def _init_known_facts(self, conn):
        """Инициализация базы знаний — НЕ заполняем предзаполненными данными.
        Система сама накапливает знания через тестирование и использование."""
        # База знаний начинается пустой — агенты сами накапливают опыт
        # Это честно: verified=0 означает "не проверено"
        pass
    
    def record_attempt(self, method_name: str, success: bool):
        """Записывает попытку использования метода"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                success_val = 1 if success else 0
                conn.execute("""
                    INSERT INTO api_methods (method_name, code_template, attempts, successes, last_used)
                    VALUES (?, '', 1, ?, datetime('now'))
                    ON CONFLICT(method_name) DO UPDATE SET
                        attempts = attempts + 1,
                        successes = successes + ?,
                        last_used = datetime('now'),
                        success_rate = CAST(successes AS REAL) / attempts
                """, (method_name, success_val, success_val))
    
    def record_error(self, error_message: str, solution: Optional[str] = None):
        """Записывает ошибку и возможное решение"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Проверяем существование
                cursor = conn.execute(
                    "SELECT id FROM error_patterns WHERE error_message = ?",
                    (error_message,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    conn.execute("""
                        UPDATE error_patterns 
                        SET frequency = frequency + 1, last_seen = datetime('now')
                        WHERE id = ?
                    """, (existing[0],))
                else:
                    conn.execute("""
                        INSERT INTO error_patterns (error_message, solution, last_seen)
                        VALUES (?, ?, datetime('now'))
                    """, (error_message, solution))
    
    def record_solution(self, task_description: str, solution_code: str):
        """Записывает рабочее решение"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO working_solutions (task_description, solution_code, last_used)
                    VALUES (?, ?, datetime('now'))
                """, (task_description, solution_code))
    
    def get_best_method(self, task_type: str) -> Optional[dict]:
        """Возвращает лучший метод для задачи"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT method_name, code_template, success_rate, notes
                FROM api_methods
                WHERE method_name LIKE ?
                ORDER BY success_rate DESC, attempts DESC
                LIMIT 1
            """, (f"%{task_type}%",))
            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "template": row[1],
                    "success_rate": row[2],
                    "notes": row[3]
                }
        return None
    
    def get_all_methods(self) -> list[dict]:
        """Возвращает все методы с их статистикой"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT method_name, code_template, success_rate, attempts, successes, notes
                FROM api_methods
                ORDER BY success_rate DESC
            """)
            return [
                {
                    "name": row[0],
                    "template": row[1],
                    "success_rate": row[2],
                    "attempts": row[3],
                    "successes": row[4],
                    "notes": row[5]
                }
                for row in cursor.fetchall()
            ]
    
    def find_similar_error(self, error_message: str) -> Optional[dict]:
        """Ищет похожую ошибку в базе"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT error_message, solution, frequency
                FROM error_patterns
                WHERE error_message LIKE ?
                ORDER BY frequency DESC
                LIMIT 1
            """, (f"%{error_message[:50]}%",))
            row = cursor.fetchone()
            if row:
                return {
                    "error": row[0],
                    "solution": row[1],
                    "frequency": row[2]
                }
        return None
    
    def get_object_class_info(self, class_name: str) -> Optional[dict]:
        """Возвращает информацию о классе объекта"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT class_name, create_method, required_params, notes, verified
                FROM object_classes
                WHERE class_name = ?
            """, (class_name,))
            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "create_method": row[1],
                    "params": row[2],
                    "notes": row[3],
                    "verified": bool(row[4])
                }
        return None
    
    def get_all_classes(self) -> list[dict]:
        """Возвращает все известные классы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT class_name, create_method, required_params, notes, verified
                FROM object_classes
                ORDER BY verified DESC, class_name
            """)
            return [
                {
                    "name": row[0],
                    "create_method": row[1],
                    "params": row[2],
                    "notes": row[3],
                    "verified": bool(row[4])
                }
                for row in cursor.fetchall()
            ]
    
    def add_new_class(self, class_name: str, create_method: str, params: Optional[str] = None, notes: str = ""):
        """Добавляет новый класс в базу"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO object_classes 
                    (class_name, create_method, required_params, notes, verified)
                    VALUES (?, ?, ?, ?, 1)
                """, (class_name, create_method, params, notes))
    
    def export_knowledge(self) -> dict:
        """Экспортирует всю базу знаний"""
        return {
            "methods": self.get_all_methods(),
            "classes": self.get_all_classes(),
            "exported_at": datetime.now().isoformat()
        }
    
    def import_knowledge(self, data: dict):
        """Импортирует базу знаний"""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                for method in data.get("methods", []):
                    conn.execute("""
                        INSERT OR REPLACE INTO api_methods 
                        (method_name, code_template, success_rate, notes)
                        VALUES (?, ?, ?, ?)
                    """, (method["name"], method["template"], method["success_rate"], method.get("notes", "")))
                
                for cls in data.get("classes", []):
                    conn.execute("""
                        INSERT OR REPLACE INTO object_classes 
                        (class_name, create_method, required_params, notes, verified)
                        VALUES (?, ?, ?, ?, ?)
                    """, (cls["name"], cls["create_method"], cls.get("params"), cls.get("notes", ""), cls.get("verified", 0)))
                
                conn.commit()


# Глобальный экземпляр базы знаний
kb = KnowledgeBase()
