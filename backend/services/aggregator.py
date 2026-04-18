from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Iterable, Optional

import httpx

from .job_apis import (
    AdzunaSource,
    Job,
    JobSource,
    JoobleSource,
    JSearchSource,
    RemotiveSource,
    SearchQuery,
)

log = logging.getLogger(__name__)


@dataclass
class SourceResult:
    source: str
    jobs: list[Job]
    error: Optional[str] = None


class JobAggregator:
    """Fan out a SearchQuery across all configured sources, then dedupe by fingerprint."""

    def __init__(self, sources: Optional[Iterable[JobSource]] = None):
        if sources is None:
            sources = self._default_sources()
        self.sources: list[JobSource] = list(sources)

    @staticmethod
    def _default_sources() -> list[JobSource]:
        client = httpx.AsyncClient(timeout=20.0)
        sources: list[JobSource] = []
        for cls in (AdzunaSource, JSearchSource, JoobleSource):
            try:
                sources.append(cls(client=client))
            except RuntimeError as e:
                log.warning("Skipping %s: %s", cls.__name__, e)
        sources.append(RemotiveSource(client=client))
        return sources

    async def close(self) -> None:
        await asyncio.gather(*(s.close() for s in self.sources), return_exceptions=True)

    async def search(
        self, query: SearchQuery, pages: int = 1
    ) -> tuple[list[Job], list[SourceResult]]:
        tasks = []
        for source in self.sources:
            for page in range(1, pages + 1):
                q = query.model_copy(update={"page": page})
                tasks.append(self._safe_search(source, q))

        results = await asyncio.gather(*tasks)
        deduped = self._dedupe(j for r in results for j in r.jobs)
        return deduped, results

    @staticmethod
    async def _safe_search(source: JobSource, query: SearchQuery) -> SourceResult:
        try:
            jobs = await source.search(query)
            return SourceResult(source=source.name, jobs=jobs)
        except Exception as e:
            log.warning("Source %s failed: %s", source.name, e)
            return SourceResult(source=source.name, jobs=[], error=str(e))

    @staticmethod
    def _dedupe(jobs: Iterable[Job]) -> list[Job]:
        seen: dict[str, Job] = {}
        for job in jobs:
            fp = job.fingerprint
            existing = seen.get(fp)
            if existing is None:
                seen[fp] = job
                continue
            if (job.description or "") and len(job.description or "") > len(existing.description or ""):
                seen[fp] = job
        return list(seen.values())
