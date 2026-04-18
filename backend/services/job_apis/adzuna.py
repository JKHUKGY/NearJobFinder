from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from .base import Job, JobSource, SearchQuery

ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"


class AdzunaSource(JobSource):
    """https://developer.adzuna.com/ — 1000 free calls/month."""

    name = "adzuna"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        country: str = "us",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.app_id = app_id or os.getenv("ADZUNA_APP_ID")
        self.app_key = app_key or os.getenv("ADZUNA_APP_KEY")
        self.country = country.lower()
        if not (self.app_id and self.app_key):
            raise RuntimeError("Adzuna credentials missing: set ADZUNA_APP_ID and ADZUNA_APP_KEY")

    async def search(self, query: SearchQuery) -> list[Job]:
        url = f"{ADZUNA_BASE}/{self.country}/search/{query.page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query.keywords,
            "results_per_page": min(query.results_per_page, 50),
            "content-type": "application/json",
        }
        if query.location:
            params["where"] = query.location
            params["distance"] = query.radius_km
        if query.remote_only:
            params["what_or"] = "remote"

        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return [self._parse(item) for item in data.get("results", [])]

    def _parse(self, item: dict) -> Job:
        loc = item.get("location") or {}
        company = item.get("company") or {}
        created = item.get("created")
        posted = None
        if created:
            try:
                posted = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                posted = None
        return Job(
            source=self.name,
            source_id=str(item.get("id")),
            title=item.get("title", "").strip(),
            company=company.get("display_name"),
            location=loc.get("display_name"),
            description=item.get("description"),
            url=item.get("redirect_url", ""),
            salary_min=item.get("salary_min"),
            salary_max=item.get("salary_max"),
            salary_currency="USD" if self.country == "us" else None,
            posted_at=posted,
            raw=item,
        )
