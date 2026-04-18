"""Generate a PDF listing jobs from one or more keyword searches.

    python -m scripts.generate_pdf \\
        "electrical engineering intern,computer engineering intern,hardware intern" \\
        --location "Seattle, WA" --radius 50 --pages 2 --count 30 \\
        --output reports/ece-seattle.pdf
"""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from backend.services.aggregator import JobAggregator
from backend.services.job_apis import Job, SearchQuery


async def gather_jobs(
    keywords_list: list[str],
    location: str,
    radius_km: int,
    pages: int,
    delay: float = 1.5,
) -> list[Job]:
    aggregator = JobAggregator()
    collected: list[Job] = []
    try:
        for idx, kw in enumerate(keywords_list):
            if idx > 0 and delay > 0:
                await asyncio.sleep(delay)
            query = SearchQuery(
                keywords=kw,
                location=location,
                radius_km=radius_km,
                results_per_page=50,
            )
            jobs, _ = await aggregator.search(query, pages=pages)
            collected.extend(jobs)
            print(f"  '{kw}' → {len(jobs)} jobs")
    finally:
        await aggregator.close()

    seen: dict[str, Job] = {}
    for j in collected:
        if j.fingerprint not in seen:
            seen[j.fingerprint] = j
    return list(seen.values())


def esc(s: str | None) -> str:
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_salary(lo: float | None, hi: float | None, ccy: str | None) -> str:
    sym = {"USD": "$", "EUR": "€", "GBP": "£"}.get(ccy or "USD", "")
    if lo and hi and lo != hi:
        return f"{sym}{lo:,.0f}–{sym}{hi:,.0f}"
    if lo:
        return f"{sym}{lo:,.0f}"
    if hi:
        return f"{sym}{hi:,.0f}"
    return ""


def build_pdf(jobs: list[Job], output_path: Path, title: str) -> None:
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=title,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=18, spaceAfter=14)
    h2 = ParagraphStyle(
        "JobTitle",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=2,
        textColor=colors.HexColor("#1a1a1a"),
    )
    meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#444"),
        spaceAfter=2,
    )
    link = ParagraphStyle(
        "Link",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#0066cc"),
        spaceAfter=10,
    )

    story = [Paragraph(esc(title), title_style)]
    for i, job in enumerate(jobs, 1):
        story.append(Paragraph(f"{i}. {esc(job.title)}", h2))

        meta_parts: list[str] = []
        if job.company:
            meta_parts.append(f"<b>{esc(job.company)}</b>")
        if job.location:
            meta_parts.append(esc(job.location))
        salary = format_salary(job.salary_min, job.salary_max, job.salary_currency)
        if salary:
            meta_parts.append(salary)
        if job.is_remote:
            meta_parts.append("Remote")
        meta_parts.append(f"[{job.source}]")
        story.append(Paragraph(" · ".join(meta_parts), meta))

        if job.url:
            story.append(
                Paragraph(f'<link href="{esc(job.url)}">{esc(job.url)}</link>', link)
            )
        else:
            story.append(Spacer(1, 6))

    doc.build(story)


def main() -> None:
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("keywords", help="comma-separated keywords")
    p.add_argument("--location", required=True)
    p.add_argument("--radius", type=int, default=50)
    p.add_argument("--pages", type=int, default=2)
    p.add_argument("--count", type=int, default=30)
    p.add_argument("--output", default="reports/jobs.pdf")
    p.add_argument("--title", default=None)
    p.add_argument("--delay", type=float, default=1.5,
                   help="seconds between keyword searches (avoid 429)")
    args = p.parse_args()

    kw_list = [k.strip() for k in args.keywords.split(",") if k.strip()]
    print(f"Searching {len(kw_list)} keyword(s) in {args.location} (radius {args.radius}km)")
    jobs = asyncio.run(
        gather_jobs(kw_list, args.location, args.radius, args.pages, args.delay)
    )
    print(f"\nDeduped total: {len(jobs)} unique jobs")

    jobs = jobs[: args.count]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    title = args.title or f"{args.keywords} — {args.location} ({len(jobs)} jobs)"
    build_pdf(jobs, output, title)
    print(f"Wrote {output.resolve()} with {len(jobs)} jobs")


if __name__ == "__main__":
    main()
