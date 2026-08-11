"""Supabase Database Integration."""
import logging
from typing import Any, Optional
import httpx

logger = logging.getLogger("promptforge.integrations.supabase")


class SupabaseClient:
    """Supabase REST API client."""

    def __init__(self, project_url: str, api_key: str):
        if not project_url or not api_key:
            raise ValueError("Supabase project_url and api_key are required")
        self.project_url = project_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.project_url,
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def health_check(self) -> bool:
        """Check if Supabase is reachable."""
        try:
            client = await self._get_client()
            response = await client.get("/rest/v1/")
            return response.status_code == 200
        except Exception:
            return False

    async def insert(self, table: str, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a row into a table."""
        client = await self._get_client()
        response = await client.post(f"/rest/v1/{table}", json=data)
        response.raise_for_status()
        return response.json()

    async def select(self, table: str, filters: dict[str, Any] = None) -> list[dict[str, Any]]:
        """Select rows from a table."""
        client = await self._get_client()
        params = filters or {}
        response = await client.get(f"/rest/v1/{table}", params=params)
        response.raise_for_status()
        return response.json()

    async def update(self, table: str, filters: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
        """Update rows in a table."""
        client = await self._get_client()
        response = await client.patch(f"/rest/v1/{table}", params=filters, json=data)
        response.raise_for_status()
        return response.json()

    async def delete(self, table: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Delete rows from a table."""
        client = await self._get_client()
        response = await client.delete(f"/rest/v1/{table}", params=filters)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()