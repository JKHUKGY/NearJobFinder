# NearJobFinder

Aggregates job listings from multiple free APIs (Adzuna, JSearch, Jooble, Remotive),
dedupes them, and is the data backbone for personalized resume-aware advice +
PDF report generation.

## Sources

| Source | Free tier | Key required |
|---|---|---|
| [Adzuna](https://developer.adzuna.com/) | 1000 calls/month | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| [JSearch (RapidAPI)](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) | 200 calls/month | `RAPIDAPI_KEY` |
| [Jooble](https://jooble.org/api/about) | free, request a key | `JOOBLE_API_KEY` |
| [Remotive](https://remotive.com/api-documentation) | unlimited (remote only) | none |

Sources without credentials are silently skipped at startup, so you can begin
with just one and add the rest later.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in whichever keys you have
```

## Try it

```bash
python -m scripts.search_jobs "software engineer" --location "Boston, MA" --pages 2
python -m scripts.search_jobs "data analyst" --remote
```

## Layout

```
backend/services/
├── job_apis/
│   ├── base.py        # Job model, SearchQuery, JobSource ABC
│   ├── adzuna.py
│   ├── jsearch.py
│   ├── jooble.py
│   └── remotive.py
└── aggregator.py      # parallel fan-out + dedupe by (company, title, location)
scripts/search_jobs.py # CLI demo
```

## Roadmap

- [ ] Postgres persistence + scheduled refresh
- [ ] Resume upload + Claude-based parsing
- [ ] Conversational advice endpoint
- [ ] PDF report generation (WeasyPrint)
- [ ] Multi-user auth
