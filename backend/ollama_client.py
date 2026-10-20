"""
Клиент для локальной LLM Ollama (qwen2.5-coder:7b)
"""

import httpx
from typing import Optional

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2.5-coder:7b"


class OllamaClient:
    """Клиент для Ollama API"""
    
    def __init__(self, url: str = OLLAMA_URL, model: str = MODEL):
        self.url = url
        self.model = model
        self._healthy = None
    
    async def check_health(self) -> bool:
        """Проверяет доступность Ollama"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.url}/api/tags")
                self._healthy = r.status_code == 200
                return self._healthy
        except Exception:
            self._healthy = False
            return False
    
    async def generate(self, prompt: str, system: str = "") -> str:
        """Генерирует ответ на промпт"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 2048,
            }
        }
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{self.url}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("response", "")
    
    async def chat(self, messages: list[dict]) -> str:
        """Chat-режим (если нужен)"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{self.url}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("message", {}).get("content", "")
    
    async def list_models(self) -> list[str]:
        """Список доступных моделей"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self.url}/api/tags")
                data = r.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []
