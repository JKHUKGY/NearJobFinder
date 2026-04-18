from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Optional

from .base import Job, JobSource, SearchQuery

JOOBLE_URL = "https://jooble.org/api/{key}"
SALARY_RE = re.compile(r"(\d[\d,\.]*)")


class JoobleSource(JobSource):
    """https://jooble.org/api/about — free with API key request."""

    name = "jooble"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("JOOBLE_API_KEY")
        if not self.api_key:
            raise RuntimeError("Jooble needs JOOBLE_API_KEY")

    async def search(self, query: SearchQuery) -> list[Job]:
        url = JOOBLE_URL.format(key=self.api_key)
        payload = {
            "keywords": query.keywords,
            "location": query.location or "",
            "radius": str(query.radius_km),
            "page": str(query.page),
            "ResultOnPage": str(min(query.results_per_page, 50)),
        }
        resp = await self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return [self._parse(item) for item in data.get("jobs", [])]

    def _parse(self, item: dict) -> Job:
        salary_min, salary_max = self._parse_salary(item.get("salary"))
        updated = item.get("updated")
        posted = None
        if updated:
            try:
                posted = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            except ValueError:
                posted = None

        return Job(
            source=self.name,
            source_id=str(item.get("id", "")),
            title=(item.get("title") or "").strip(),
            company=item.get("company"),
            location=item.get("location"),
            description=item.get("snippet"),
            url=item.get("link", ""),
            salary_min=salary_min,
            salary_max=salary_max,
            posted_at=posted,
            raw=item,
        )

    @staticmethod
    def _parse_salary(text: Optional[str]) -> tuple[Optional[float], Optional[float]]:
        if not text:
            return None, None
        nums = [float(n.replace(",", "")) for n in SALARY_RE.findall(text)]
        if not nums:
            return None, None
        if len(nums) == 1:
            return nums[0], None
        return min(nums), max(nums)
