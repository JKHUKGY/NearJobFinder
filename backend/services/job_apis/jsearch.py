from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from .base import Job, JobSource, SearchQuery

JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_URL = f"https://{JSEARCH_HOST}/search"


class JSearchSource(JobSource):
    """https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch — aggregates Google for Jobs (LinkedIn, Indeed, etc.)."""

    name = "jsearch"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise RuntimeError("JSearch needs RAPIDAPI_KEY")

    async def search(self, query: SearchQuery) -> list[Job]:
        q_parts = [query.keywords]
        if query.location:
            q_parts.append(f"in {query.location}")
        params = {
            "query": " ".join(q_parts),
            "page": str(query.page),
            "num_pages": "1",
            "date_posted": "month",
        }
        if query.remote_only:
            params["work_from_home"] = "true"

        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": JSEARCH_HOST,
        }
        resp = await self._client.get(JSEARCH_URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return [self._parse(item) for item in data.get("data", [])]

    def _parse(self, item: dict) -> Job:
        location_parts = [
            item.get("job_city"),
            item.get("job_state"),
            item.get("job_country"),
        ]
        location = ", ".join(p for p in location_parts if p) or None

        posted_ts = item.get("job_posted_at_timestamp")
        posted = (
            datetime.fromtimestamp(posted_ts, tz=timezone.utc) if posted_ts else None
        )

        return Job(
            source=self.name,
            source_id=str(item.get("job_id", "")),
            title=item.get("job_title", "").strip(),
            company=item.get("employer_name"),
            location=location,
            description=item.get("job_description"),
            url=item.get("job_apply_link") or item.get("job_google_link", ""),
            salary_min=item.get("job_min_salary"),
            salary_max=item.get("job_max_salary"),
            salary_currency=item.get("job_salary_currency"),
            is_remote=bool(item.get("job_is_remote")),
            posted_at=posted,
            raw=item,
        )
