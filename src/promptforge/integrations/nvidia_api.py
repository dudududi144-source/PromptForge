"""NVIDIA Build API Client."""
import json
import logging
from typing import Any, Optional
import httpx

logger = logging.getLogger("promptforge.integrations.nvidia")

MODEL_REGISTRY = {
    "glm-5.2": {"id": "z-ai/glm-5.2", "max_tokens": 131072},
    "llama-8b": {"id": "meta/llama-3.1-8b-instruct", "max_tokens": 131072},
    "llama-70b": {"id": "meta/llama-3.1-70b-instruct", "max_tokens": 131072},
}


class NVIDIAAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"NVIDIA API Error {status_code}: {message}")


class NVIDIAAPIClient:
    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self, api_key: str, timeout: float = 120.0):
        if not api_key:
            raise ValueError("NVIDIA API key is required")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=self.timeout,
            )
        return self._client

    async def chat_completion(
        self, messages: list[dict[str, str]], model: str = "glm-5.2",
        temperature: float = 0.1, max_tokens: int = 4096, task_type: str = "general"
    ) -> dict[str, Any]:
        model_config = MODEL_REGISTRY.get(model)
        if not model_config:
            raise ValueError(f"Unknown model: {model}")
        payload = {
            "model": model_config["id"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": min(max_tokens, model_config["max_tokens"]),
        }
        client = await self._get_client()
        try:
            response = await client.post("/chat/completions", json=payload)
            if response.status_code == 429:
                raise NVIDIAAPIError(429, "Rate limit exceeded")
            if response.status_code == 401:
                raise NVIDIAAPIError(401, "Invalid API key")
            if response.status_code != 200:
                raise NVIDIAAPIError(response.status_code, response.text[:500])
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            return {"content": content, "model": model, "tokens_used": usage.get("total_tokens", 0)}
        except httpx.TimeoutException:
            raise NVIDIAAPIError(408, f"Timeout after {self.timeout}s")
        except httpx.HTTPError as exc:
            raise NVIDIAAPIError(500, f"HTTP error: {exc}")

    async def structured_output(self, prompt: str, system_prompt: str = "Respond with valid JSON only.", model: str = "glm-5.2", task_type: str = "general") -> dict[str, Any]:
        result = await self.chat_completion(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            model=model, temperature=0.0, max_tokens=4096, task_type=task_type,
        )
        content = result.get("content", "").strip()
        fence = chr(96) * 3
        if content.startswith(fence):
            lines = content.split("\n")
            json_lines = [l for l in lines if not l.strip().startswith(fence)]
            content = "\n".join(json_lines)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content}

    async def ping(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get("/models")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()