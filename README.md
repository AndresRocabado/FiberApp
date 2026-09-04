# Fiber Network Management System

A web application for managing fiber optic network infrastructure — nodes, links, cities, and operational status. Built with a FastAPI backend and a vanilla HTML/CSS/JS single-page frontend.

## Features

- **Node management** — create, edit, soft-delete, and restore nodes with type and status badges
- **Link management** — manage connections between nodes with distance and capacity tracking
- **Dashboard** — live metrics, charts (nodes by city, link status), and isolated-node warnings
- **Reports** — network summary with CSV export
- **Trash / restore** — soft-deleted records are recoverable from a dedicated trash page
- **Search & filter** — real-time client-side filtering with debounce on all tables
- **Pagination** — 20 records per page with Previous / Next controls
- **Dark mode** — toggle with persistence via `localStorage`
- **Bilingual UI** — Spanish and English, switchable at runtime
- **Authentication** — JWT-based login; all API routes are protected

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Database | SQLite |
| Frontend | Vanilla HTML, CSS, JavaScript (no framework) |
| Auth | PyJWT, python-dotenv |
| Tests | pytest |

## Project Structure

```
fiber-network-system/
├── api/
│   ├── main.py               # FastAPI app entry point
│   ├── auth.py               # JWT login endpoint + auth dependency
│   ├── schemas.py            # Pydantic request/response models
│   └── routers/
│       ├── nodes.py
│       ├── links.py
│       └── reports.py
├── src/
│   ├── models/               # Dataclasses + enums (Node, FiberLink)
│   ├── repositories/         # SQLite data access layer
│   ├── services/             # Business logic
│   └── utils/
│       └── csv_exporter.py
├── database/
│   ├── connection.py         # SQLite connection context manager
│   └── schema.py             # Table creation + migrations
├── frontend/
│   ├── index.html            # SPA shell
│   ├── css/styles.css
│   ├── js/
│   │   ├── api.js            # Fetch wrapper (auth header + 401 handling)
│   │   ├── i18n.js           # Locale loader
│   │   └── pages/            # dashboard, nodes, links, reports, trash
│   └── locales/
│       ├── es.json
│       └── en.json
├── tests/
├── .env                      # Credentials (not committed)
├── .env.example
└── requirements.txt
```

## Getting Started

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd fiber-network-system

python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / Mac
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure credentials

Copy `.env.example` to `.env` and edit it:

```bash
cp .env.example .env
```

```env
APP_USERNAME=admin
APP_PASSWORD=your_password
JWT_SECRET=a-long-random-secret-string
JWT_EXPIRE_HOURS=8
```

### 4. Run the server

```bash
uvicorn api.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Authentication

All API routes under `/api/` require a valid JWT token. The login page is shown automatically when no token is present or when the session expires. Credentials are configured in `.env` — no database of users is needed.

## Running Tests

```bash
pytest tests/ -v
```

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_USERNAME` | Login username | `admin` |
| `APP_PASSWORD` | Login password | `admin123` |
| `JWT_SECRET` | Secret key used to sign tokens | `change-me` |
| `JWT_EXPIRE_HOURS` | Session duration in hours | `8` |
| `DB_PATH` | SQLite database file path | `fiber_network.db` |

## Architecture

```
Browser (SPA)
    │  HTTP + JWT
FastAPI (api/)
    │
Services (src/services/)     ← business logic, validation
    │
Repositories (src/repositories/)  ← SQL queries
    │
SQLite (database/)
```
