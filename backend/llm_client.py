"""
Клиент для локальной LLM Ollama
"""

import httpx
from typing import Optional


class OllamaClient:
    """Клиент для Ollama API"""
    
    def __init__(self, url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        self.url = url
        self.model = model
    
    async def check_health(self) -> bool:
        """Проверяет доступность Ollama"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """Генерирует ответ на промпт"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
        except Exception as e:
            raise Exception(f"Ошибка генерации: {str(e)}")
    
    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """Chat-режим"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            raise Exception(f"Ошибка чата: {str(e)}")
