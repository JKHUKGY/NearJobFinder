"""CLI demo: search all configured job sources and print a summary.

    python -m scripts.search_jobs "software engineer" --location "Boston, MA" --pages 2
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter

from dotenv import load_dotenv

from backend.services.aggregator import JobAggregator
from backend.services.job_apis import SearchQuery


async def run(args: argparse.Namespace) -> None:
    aggregator = JobAggregator()
    try:
        query = SearchQuery(
            keywords=args.keywords,
            location=args.location,
            radius_km=args.radius,
            results_per_page=args.per_page,
            remote_only=args.remote,
        )
        jobs, source_results = await aggregator.search(query, pages=args.pages)
    finally:
        await aggregator.close()

    print(f"\n=== Per-source results for '{args.keywords}' ===")
    for r in source_results:
        status = f"{len(r.jobs)} jobs" if r.error is None else f"ERROR: {r.error}"
        print(f"  [{r.source:>8}] page → {status}")

    by_source = Counter(j.source for j in jobs)
    print(f"\n=== Deduped total: {len(jobs)} jobs ===")
    for src, n in by_source.most_common():
        print(f"  {src:>8}: {n}")

    print("\n=== First 10 ===")
    for j in jobs[:10]:
        salary = ""
        if j.salary_min or j.salary_max:
            salary = f" | ${j.salary_min or '?'}–${j.salary_max or '?'}"
        print(f"- [{j.source}] {j.title} @ {j.company or '?'} ({j.location or '?'}){salary}")
        print(f"    {j.url}")


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("keywords")
    p.add_argument("--location", default=None)
    p.add_argument("--radius", type=int, default=25)
    p.add_argument("--pages", type=int, default=1)
    p.add_argument("--per-page", type=int, default=50)
    p.add_argument("--remote", action="store_true")
    args = p.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
