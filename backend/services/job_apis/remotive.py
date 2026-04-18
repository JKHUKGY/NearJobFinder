from __future__ import annotations

from datetime import datetime
from typing import Optional

from .base import Job, JobSource, SearchQuery

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"


class RemotiveSource(JobSource):
    """https://remotive.com/api-documentation — fully free, remote jobs only."""

    name = "remotive"

    async def search(self, query: SearchQuery) -> list[Job]:
        params = {"search": query.keywords, "limit": query.results_per_page}
        resp = await self._client.get(REMOTIVE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        return [self._parse(item) for item in data.get("jobs", [])]

    def _parse(self, item: dict) -> Job:
        salary_min, salary_max, currency = self._parse_salary(item.get("salary"))
        pub = item.get("publication_date")
        posted: Optional[datetime] = None
        if pub:
            try:
                posted = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            except ValueError:
                posted = None
        return Job(
            source=self.name,
            source_id=str(item.get("id", "")),
            title=(item.get("title") or "").strip(),
            company=item.get("company_name"),
            location=item.get("candidate_required_location") or "Remote",
            description=item.get("description"),
            url=item.get("url", ""),
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            is_remote=True,
            posted_at=posted,
            raw=item,
        )

    @staticmethod
    def _parse_salary(text: Optional[str]):
        if not text:
            return None, None, None
        import re

        currency = None
        if "$" in text or "USD" in text.upper():
            currency = "USD"
        elif "€" in text or "EUR" in text.upper():
            currency = "EUR"
        elif "£" in text or "GBP" in text.upper():
            currency = "GBP"

        nums = [float(n.replace(",", "")) for n in re.findall(r"(\d[\d,]*)", text)]
        nums = [n for n in nums if n >= 1000]
        if not nums:
            return None, None, currency
        if len(nums) == 1:
            return nums[0], None, currency
        return min(nums), max(nums), currency
