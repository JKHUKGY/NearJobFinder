from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import httpx
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    keywords: str
    location: Optional[str] = None
    radius_km: int = 25
    page: int = 1
    results_per_page: int = 50
    remote_only: bool = False


class Job(BaseModel):
    source: str
    source_id: str
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    url: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    is_remote: bool = False
    posted_at: Optional[datetime] = None
    raw: dict = Field(default_factory=dict, exclude=True)

    @property
    def fingerprint(self) -> str:
        key = "|".join(
            [
                (self.company or "").strip().lower(),
                self.title.strip().lower(),
                (self.location or "").strip().lower(),
            ]
        )
        return hashlib.sha1(key.encode("utf-8")).hexdigest()


class JobSource(ABC):
    name: str

    def __init__(self, client: Optional[httpx.AsyncClient] = None, timeout: float = 20.0):
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "JobSource":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[Job]:
        ...
