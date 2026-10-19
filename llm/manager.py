"""
llm/manager.py - محرك استدعاء النماذج غير المتزامن (Async LLM Manager)
=====================================================================
يدعم استدعاء النماذج بشكل غير متزامن (Async) بالكامل دون تجميد FastAPI Event Loop:
- النماذج السحابية (OpenAI, Claude, Groq, Gemini) عبر LiteLLM Asynchronous API
- النماذج المحلية (Ollama) عبر httpx.AsyncClient غير المتزامن
مع الحفاظ على واجهات متزامنة (Sync) للتوافق التام مع بقية مكونات المشروع.
"""
import os
import asyncio
from typing import Optional, Dict, Any

import httpx
import litellm

from config import (
    OLLAMA_URL,
    MODEL_NAME,
    TEMPERATURE,
    TIMEOUT,
)

# كتم رسائل الـ Debug غير الضرورية من LiteLLM
litellm.suppress_debug_info = True


class LLMManager:
    """
    مدير موحد لاستدعاء نماذج الذكاء الاصطناعي (Ollama, OpenAI, Claude, Groq, Gemini).
    """

    def __init__(self):
        self.default_model = MODEL_NAME
        self.timeout = TIMEOUT
        self.temperature = TEMPERATURE

    def _is_cloud_model(self, model: str) -> bool:
        """فحص ما إذا كان النموذج سحابياً مدعوماً عبر LiteLLM"""
        cloud_identifiers = (
            "gpt-", "o1-", "o3-", "claude-", "groq/", "gemini/",
            "openai/", "anthropic/", "mistral/", "deepseek/"
        )
        model_lower = model.lower()
        return any(model_lower.startswith(prefix) for prefix in cloud_identifiers)

    async def generate_async(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        استدعاء النموذج بشكل غير متزامن (Async) دون حظر الـ FastAPI Event Loop.
        """
        selected_model = model or self.default_model
        temp = temperature if temperature is not None else self.temperature

        # 1. الاستدعاء السحابي عبر LiteLLM (OpenAI, Claude, Groq, Gemini...)
        if self._is_cloud_model(selected_model):
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = await litellm.acompletion(
                    model=selected_model,
                    messages=messages,
                    temperature=temp,
                    timeout=self.timeout,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"LiteLLM Error ({selected_model}): {str(e)}"

        # 2. الاستدعاء المحلي (Ollama) عبر httpx.AsyncClient
        try:
            payload: Dict[str, Any] = {
                "model": selected_model,
                "prompt": prompt,
                "stream": False,
                "temperature": temp,
            }
            if system_prompt:
                payload["system"] = system_prompt

            timeout_cfg = httpx.Timeout(float(self.timeout), connect=10.0)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                res = await client.post(OLLAMA_URL, json=payload)
                res.raise_for_status()
                data = res.json()
                return data.get("response", "").strip()

        except httpx.RequestError as e:
            return f"Ollama Connection Error: {str(e)}"
        except Exception as e:
            return f"LLM Generation Error: {str(e)}"

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        واجهة استدعاء متزامنة (Sync) للتوافق التام مع أي كود حالي.
        """
        selected_model = model or self.default_model
        temp = temperature if temperature is not None else self.temperature

        # النماذج السحابية عبر LiteLLM Sync
        if self._is_cloud_model(selected_model):
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = litellm.completion(
                    model=selected_model,
                    messages=messages,
                    temperature=temp,
                    timeout=self.timeout,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"LiteLLM Sync Error ({selected_model}): {str(e)}"

        # النماذج المحلية (Ollama) عبر httpx.Client المتزامن
        try:
            payload: Dict[str, Any] = {
                "model": selected_model,
                "prompt": prompt,
                "stream": False,
                "temperature": temp,
            }
            if system_prompt:
                payload["system"] = system_prompt

            timeout_cfg = httpx.Timeout(float(self.timeout), connect=10.0)
            with httpx.Client(timeout=timeout_cfg) as client:
                res = client.post(OLLAMA_URL, json=payload)
                res.raise_for_status()
                data = res.json()
                return data.get("response", "").strip()

        except httpx.RequestError as e:
            return f"Ollama Connection Error: {str(e)}"
        except Exception as e:
            return f"LLM Sync Error: {str(e)}"


# الكائن الرئيسي الموحد
llm = LLMManager()


async def generate_async(prompt: str, **kwargs) -> str:
    """دالة Async العامة للاستدعاء غير المتزامن"""
    return await llm.generate_async(prompt, **kwargs)


def generate(prompt: str, **kwargs) -> str:
    """دالة متزامنة عامة للحفاظ على التوافق التام"""
    return llm.generate(prompt, **kwargs)