# JobRadar

> An offline-first Python web application for discovering, organizing, and tracking software engineering jobs — all your data stays local.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

---

## About

JobRadar is a personal job search companion designed to simplify the software engineering job hunt.

Instead of manually checking multiple job boards every day, JobRadar **syncs vacancies from multiple providers into a local cache** and presents them in one unified dashboard where you can search, filter, bookmark, organize, and track applications.

JobRadar is **offline-first**: once a sync has run, all browsing, searching, filtering, and note-taking work entirely on locally stored data — no accounts, no sign-in, no constant network connection required. A sync is only needed when you want fresh listings.

The application **does not replace existing job boards**. You still apply through the original websites; JobRadar acts as a centralized, private platform for managing your job search.

This project is also a learning journey. It is being built incrementally to explore modern Python backend development, software architecture, API integrations, local data management, and deployment best practices.

---

## Motivation

Searching for software jobs often means juggling multiple websites:

- Bundesagentur für Arbeit
- LinkedIn
- Arbeitnow
- Himalayas
- Adzuna
- Company career pages

Each platform has different filters, search experiences, and — usually — no meaningful application tracking at all.

JobRadar solves this by syncing listings into a single local store, giving you one place to:

- Search across multiple providers
- Browse cached results without an internet connection
- Save interesting opportunities
- Track application progress
- Keep personal notes
- Refresh saved searches and spot newly posted jobs

Your search history, notes, and application status live on **your machine** — not on someone else's server.

---

## Local-First Behavior

JobRadar follows a simple storage model:

- **Sync** — job listings are fetched during a manual or scheduled sync run.
- **Local storage** — all normalized job data, user state, and notes are stored locally.
- **Offline operation** — search, filters, bookmarks, notes, and application status work entirely on cached data.
- **Original links** — every job keeps its source URL; you apply on the original website.
- **No re-authentication** — browsing cached data never requires logging in to anything.

### Storage layers

| Layer | Storage | Purpose |
|---|---|---|
| Raw cache | SQLite tables / local JSON | Original provider payloads, kept for reprocessing and debugging |
| Normalized records | SQLite (PostgreSQL later) | Queryable, deduplicated job data |
| User state | SQLite | Viewed, bookmarked, applied, notes, timestamps |
| Static assets | Local files | Frontend resources |

---

## Goals

### Primary Goal

Build a real-world portfolio project that demonstrates modern backend software engineering using Python — while producing a genuinely useful tool.

### Learning Goals

This project is intentionally designed to learn:

- Modern Python
- FastAPI
- SQLAlchemy 2
- SQLite → PostgreSQL migration path
- REST APIs
- Async programming
- Clean Architecture
- Repository Pattern
- Service Layer
- Adapter Pattern
- Caching strategies and offline-first design
- Full-text search (SQLite FTS5)
- Testing with pytest
- Database migrations (Alembic)
- Production deployment
- CI/CD fundamentals

---

## Features

### MVP

- Sync jobs from multiple providers into a local cache
- Search and filter cached jobs (keyword, provider, location)
- Offline browsing of all synced listings and details
- Save/bookmark jobs
- Application tracking (applied, interview, offer, rejected)
- Personal notes per job
- Saved searches with refresh
- New-since-last-sync highlighting
- Responsive web interface served by a local backend

### Planned Features

- Duplicate detection across providers
- Full-text search over job descriptions (SQLite FTS5)
- Company history
- Salary insights
- Job statistics and analytics dashboard
- Email notifications for new matches
- Scheduled daily sync
- AI-powered skill extraction
- Resume matching
- Export to CSV/JSON

---

## Supported Job Providers

### Initial Providers

- Bundesagentur für Arbeit (official public Jobsuche API)
- Arbeitnow
- Himalayas

### Planned Providers

- Adzuna
- Careerjet
- Additional public APIs

Every provider is isolated behind an adapter so the rest of the application remains provider-independent. Providers without a permitted API may be supported as **link-only** integrations: JobRadar builds a pre-filled search URL and opens it in the browser, without scraping.

---

## Tech Stack

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy 2
- SQLite (MVP) → PostgreSQL
- Alembic
- Pydantic v2
- httpx
- uv

### Frontend

- Jinja2
- Bootstrap 5
- HTMX

### Development

- Ruff
- pytest
- Git
- GitHub

### Hosting

- Local-first by design; Render (or similar) for optional demo deployment

---

## Project Structure

```
jobradar/
├── app/
│   ├── api/            # FastAPI routes
│   ├── core/           # Config, settings, logging
│   ├── database/       # Engine, session, base models
│   ├── adapters/       # Provider integrations (one per source)
│   ├── cache/          # Raw payload cache + sync metadata
│   ├── repositories/   # Data access layer
│   ├── services/       # Sync, search, tracking business logic
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── templates/      # Jinja2 templates
│   └── static/         # CSS, JS, assets
│
├── migrations/
├── tests/
│
├── pyproject.toml
├── README.md
└── .env.example
```

> **Note:** The project starts much simpler and evolves into this structure only when needed. Avoiding premature abstraction is an intentional design decision.

---

## Architecture

```
Browser
   │
   ▼
FastAPI (local backend)
   │
   ▼
Application Services ────────── Sync Service
   │                                │
   ▼                                ▼
Repositories                    Provider Adapters
   │                                │
   ▼                                ▼
Local Database                External Job APIs
(SQLite → PostgreSQL)         (only during sync)
   │
   ▼
Raw Cache (provider payloads)
```

### Key design decisions

- **Reads never hit the network.** The UI only queries the local database; external APIs are called exclusively by the Sync Service.
- **Raw payloads are cached.** Original provider responses are stored so data can be reprocessed without re-fetching.
- **User state is authoritative.** Bookmarks, notes, and application status are never overwritten by sync runs.
- **Adapters are interchangeable.** Each provider maps its data into a unified internal `Job` model; adding a provider never touches the rest of the app.

---

## Development Philosophy

This project follows a few simple principles:

- Build small, iterate often.
- Prefer readability over cleverness.
- Use explicit code over magic.
- Add abstractions only when they solve a real problem.
- Learn the "why" before the "how".
- Keep data local and respect each provider's terms and rate limits.
- Treat the project as if it were a real production application.

---

## Roadmap

### Phase 1 — Foundation

- [ ] Project setup
- [ ] FastAPI
- [ ] Homepage
- [ ] Bootstrap
- [ ] Demo deployment (Render)

### Phase 2 — Local Persistence

- [ ] SQLite + SQLAlchemy
- [ ] Job model + raw cache tables
- [ ] CRUD operations

### Phase 3 — First Sync

- [ ] Bundesagentur für Arbeit integration
- [ ] Sync service (fetch → cache → normalize → store)
- [ ] Job search over cached results
- [ ] Search results page

### Phase 4 — Tracking

- [ ] Save/bookmark jobs
- [ ] Application tracking
- [ ] Notes
- [ ] New-since-last-sync highlighting

### Phase 5 — Scale the Sources

- [ ] Saved searches with refresh
- [ ] Multiple providers
- [ ] Duplicate detection
- [ ] Full-text search (FTS5)

### Phase 6 — Polish

- [ ] Statistics dashboard
- [ ] CSV/JSON export
- [ ] Scheduled sync
- [ ] Optional multi-user mode (only if ever deployed publicly)

---

## Running the Project

### Clone

```bash
git clone https://github.com/<username>/jobradar.git
cd jobradar
```

### Create the environment

```bash
uv sync
```

### Run the first sync

```bash
uv run python -m app.sync
```

### Start the development server

```bash
uv run fastapi dev app/main.py
```

or

```bash
uv run uvicorn app.main:app --reload
```

Visit:

```
http://127.0.0.1:8000
```

From here on, everything works offline until you choose to sync again.

---

## Data & Privacy

- The database lives on your machine (default: `jobradar.db` in the project directory; XDG paths respected on Linux).
- No telemetry, no accounts, no tracking.
- Job-search history can be sensitive — exports and backups are explicit user actions.
- API keys (where required) are read from environment variables only and never logged.

---

## Future Ideas

Potential future enhancements include:

- AI-assisted job summaries
- Resume matching
- Company insights
- Interactive maps
- Salary comparisons
- Calendar integration
- Browser extension
- Mobile application
- Public read-only API over the local dataset

---

## Contributing

This is currently a personal learning project.

Suggestions, discussions, and constructive feedback are always welcome.

---

## License

MIT License

---

## Acknowledgements

Special thanks to the maintainers of the open-source projects that make this application possible:

- FastAPI
- SQLAlchemy
- HTMX
- Bootstrap
- PostgreSQL & SQLite
- Render
- uv

And to the Bundesagentur für Arbeit for providing a public job search API.

---

## Author

**Andrea Maestri**
