# ITVM — Intelligent Traffic Violation Monitoring

> **ITVM** (Intelligent Traffic Violation Monitoring) is an end-to-end platform for detecting, reviewing, and issuing traffic violations from camera evidence. It pairs AI-based vehicle / license-plate / violation detection with a supervised human-review workflow and a fully Arabic, right-to-left (RTL) operations console.

<div dir="rtl">

**ITVM** منصة ذكية لمراقبة المخالفات المرورية. تقوم باستقبال صور الأحداث من كاميرات المرور، ثم تكتشف المركبات واللوحات والمخالفات بالذكاء الاصطناعي، وتربط كل مخالفة بالمركبة واللوحة الخاصة بها، وتتيح للمشرف مراجعة الحالة وإصدارها أو رفضها أو تصعيدها — مع لوحة تحكم عربية كاملة باتجاه من اليمين إلى اليسار.

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Installation (Docker Compose)](#installation-docker-compose)
- [Local Development](#local-development)
- [Default Accounts](#default-accounts)
- [Service Endpoints](#service-endpoints)
- [Testing & Build Verification](#testing--build-verification)
- [AI Models & Git LFS](#ai-models--git-lfs)
- [Internal Naming Note](#internal-naming-note)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

ITVM automates the lifecycle of a traffic-violation case, from raw camera evidence to a reviewed, issued (or rejected) record:

1. **Ingests** traffic images / events from registered camera devices.
2. **Detects** vehicles, license plates, and violations using AI inference models.
3. **Reads** Arabic license plates (letters + digits) with per-token confidence.
4. **Associates** each detected violation with the correct vehicle and plate.
5. **Routes** cases through a policy engine into the right state — ready for direct issue, requiring supervisor review, or flagged as no-violation.
6. **Supports supervisor review** — operators can correct the plate, adjust the violation type, add notes, and then **issue**, **reject**, or **escalate** a case.
7. **Surfaces** everything through an Arabic RTL console: dashboard, review queue, history, reports, system health, settings, and user/device administration.
8. **Stores** evidence images in object storage and records every action in an immutable audit trail.

---

## Key Features

- **Arabic RTL admin console** — a polished, right-to-left operations UI with a consistent design system.
- **Case review workflow** — guided save → review → decision (issue / reject / escalate) flow with state-aware action buttons.
- **Per-violation confidence** — every violation shows its own confidence badge; plate/vehicle confidence is used only as a fallback when no violation record exists.
- **Multiple violations per case** — each rendered independently in details, history, and the review queue.
- **License-plate reading & manual correction** — Arabic plate letters/digits are reconstructed and can be manually overridden by an operator.
- **Evidence panels** — original, annotated, violations-only, driver-zoom, and plate-crop images, with graceful fallbacks for missing assets.
- **Review queue** — search + pagination, clear human-readable reason tags, and inline approve/reject/edit actions.
- **Operational history** — filter by state, search by case number / plate, and paginate large datasets.
- **Reports** — aggregate counts and Arabic violation breakdowns, with CSV export (UTF-8 BOM for correct Arabic in Excel).
- **System health** — live status of backend, database, object storage, message queue, worker, and AI models.
- **Admin settings** — tunable policy thresholds (confidence, review, direct-issue, association) driven by the database.
- **User & device management** — create operators/supervisors and register camera devices with rotatable tokens.
- **Audit trail** — every case decision and edit is recorded with actor, role, and timestamp.
- **Dockerized deployment** — the entire stack starts with a single `docker compose up`.

---

## Architecture

ITVM is a service-oriented system orchestrated by Docker Compose. The backend handles synchronous API traffic, while heavy AI inference is offloaded to an asynchronous Celery worker via RabbitMQ.

```
                         ┌──────────────────────────┐
                         │      User Browser        │
                         │   (Arabic RTL console)   │
                         └────────────┬─────────────┘
                                      │ HTTP
                                      ▼
                         ┌──────────────────────────┐
                         │   Frontend (React/Vite)  │
                         │      nginx :8080         │
                         └────────────┬─────────────┘
                                      │ REST /api/v1
                                      ▼
                         ┌──────────────────────────┐
                         │   Backend API (FastAPI)  │
                         │          :8000           │
                         └───┬───────────┬──────┬───┘
                             │           │      │
              ┌──────────────┘           │      └───────────────┐
              ▼                          ▼                      ▼
   ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
   │  PostgreSQL :5432  │   │   MinIO  :9000     │   │  RabbitMQ :5672     │
   │  cases / audit /   │   │  evidence images   │   │  task queue         │
   │  settings / users  │   │  (object storage)  │   │                     │
   └────────────────────┘   └────────────────────┘   └─────────┬──────────┘
                                                                │ consumes
                                                                ▼
                                                  ┌────────────────────────┐
                                                  │   Celery Worker        │
                                                  │   AI inference:        │
                                                  │   vehicle / plate /    │
                                                  │   violation detection  │
                                                  └────────────────────────┘
```

**Flow:** the browser talks only to the frontend, which proxies REST calls to the FastAPI backend. The backend persists state in PostgreSQL, stores evidence in MinIO, and enqueues inference jobs on RabbitMQ. The Celery worker consumes those jobs, runs the AI models, and writes detections back — which the backend then exposes to the console.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 19 + Vite + TypeScript | Arabic RTL operations console (SPA) |
| Frontend data | TanStack Query, Axios | Server-state caching, API calls |
| Web server | nginx | Serves the built frontend bundle |
| Backend API | FastAPI (Python) | REST API, auth, case workflow |
| ORM / Migrations | SQLAlchemy + Alembic | Data models and schema migrations |
| Database | PostgreSQL 16 | Cases, violations, audit, settings, users |
| Message queue | RabbitMQ 3.13 | Decouples API from AI inference |
| Async worker | Celery | Runs AI inference jobs |
| AI inference | YOLO-based `.pt` models | Vehicle / plate / violation detection |
| Object storage | MinIO | Evidence image storage (S3-compatible) |
| Orchestration | Docker Compose | One-command multi-service deployment |

---

## Repository Structure

```
.
├── frontend/                # React + Vite + TypeScript RTL console
│   └── src/
│       ├── pages/           # Dashboard, ReviewQueue, CaseDetails, History, Reports, ...
│       ├── components/      # ConfidenceBadge, StatusBadge, EmptyState, EvidencePanel, ...
│       ├── services/        # API clients (cases, dashboard, reports, admin, ...)
│       └── app/             # Router, types, presentation helpers, global CSS
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/routes/      # cases, dashboard, reports, health, auth, admin, ...
│   │   ├── services/        # case_service, dashboard_service, health_service, ...
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   └── db/              # session, seed
│   ├── migrations/          # Alembic migrations
│   └── tests/               # pytest suite
├── worker/                  # Celery worker
│   └── app/
│       ├── celery_app.py    # Celery application
│       ├── tasks.py         # Inference tasks
│       └── inference/       # Model loading & detection pipeline
├── common/                  # Shared constants & utilities (violation catalog, policy, enums)
├── infra/docker/            # Dockerfiles (backend, worker, frontend) + nginx config
├── Ai_models/               # AI model weights (*.pt) — tracked via Git LFS (see note below)
├── docs/                    # Supplementary docs (architecture, setup, demo guide, API)
├── scripts/                 # Helper scripts (e.g. bulk_ingest.ps1)
├── test-images/             # Sample evidence images for demos/testing
├── test_images3/            # Additional sample evidence images
├── docker-compose.yml       # Production-style stack
├── docker-compose.dev.yml   # Dev overrides (hot-reload backend/worker/frontend)
├── .env.example             # Safe environment template (copy to .env)
└── .gitattributes           # Git LFS rules + line-ending normalization
```

---

## Prerequisites

| Tool | Required for | Notes |
|------|--------------|-------|
| **Docker** | Running the full stack | Required |
| **Docker Compose** | Orchestration | Bundled with modern Docker Desktop |
| **Git** | Cloning the repo | Required |
| **Git LFS** | Fetching AI model weights | Required to pull `Ai_models/*.pt` |
| Node.js 20+ | Local frontend dev only | Optional (Docker handles it otherwise) |
| Python 3.11+ | Local backend dev only | Optional (Docker handles it otherwise) |
| GitHub CLI (`gh`) | Maintainers / repo admin | Optional |

---

## Environment Variables

The stack is configured entirely through environment variables. A safe template with placeholder values is provided in **`.env.example`**.

> ⚠️ **Never commit your real `.env` file.** It is git-ignored by default. Only `.env.example` (with placeholders) belongs in version control.

Create your local `.env` from the template:

```bash
# macOS / Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

Key variables (see `.env.example` for the full list):

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | App secret for token signing — **set a strong unique value** |
| `DATABASE_URL` | PostgreSQL connection string |
| `RABBITMQ_URL` | RabbitMQ broker URL |
| `MINIO_ENDPOINT` | MinIO host:port |
| `MINIO_BUCKET` | Evidence storage bucket name |
| `FRONTEND_ORIGIN` | Allowed frontend origin |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins |
| `VIOLATION_MODEL_PATH` | Path to the violation-detection model |
| `PLATE_MODEL_PATH` | Path to the plate-detection model |
| `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD` | Seeded admin account |
| `DEFAULT_SUPERVISOR_USERNAME` / `DEFAULT_SUPERVISOR_PASSWORD` | Seeded supervisor account |
| `DEMO_DEVICE_CODE` / `DEMO_DEVICE_NAME` / `DEMO_DEVICE_TOKEN` | Seeded demo camera device |

> 🔐 For any real deployment, change `SECRET_KEY`, all default passwords, the MinIO credentials, and the demo device token before going live.

---

## Installation (Docker Compose)

```bash
git clone https://github.com/RavenS404/ITVM.git
cd ITVM

# Fetch the AI model weights (tracked via Git LFS)
git lfs install
git lfs pull

# Configure environment
cp .env.example .env        # (PowerShell: Copy-Item .env.example .env)

# Build and start the full stack
docker compose up -d --build
```

Then open the console at **http://localhost:8080**.

The backend container automatically applies database migrations and seeds the default accounts/device on first start.

To stop the stack:

```bash
docker compose down          # keep data volumes
docker compose down -v       # also remove postgres/rabbitmq/minio volumes (full reset)
```

Check service status:

```bash
docker compose ps
```

---

## Local Development

For hot-reloading backend, worker, and a Vite dev server, layer the dev override file on top of the base compose file:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

In dev mode:
- the **backend** runs with `--reload` and re-applies migrations/seed on start,
- the **worker** runs Celery with live-mounted code,
- a **frontend-dev** service runs the Vite dev server on port `8080` with polling-based hot reload.

---

## Default Accounts

The seed step creates two demo accounts (values come from your `.env`):

| Role | Username | Default Password |
|------|----------|------------------|
| Admin | `admin` | `Admin@123456` |
| Supervisor | `supervisor` | `Supervisor@123456` |

> These defaults are for local demos only. **Change them for any non-local environment.**

---

## Service Endpoints

| Service | URL | Notes |
|---------|-----|-------|
| Frontend console | http://localhost:8080 | Arabic RTL UI |
| Backend API | http://localhost:8000 | REST API under `/api/v1` |
| API docs (Swagger) | http://localhost:8000/docs | FastAPI interactive docs |
| RabbitMQ management | http://localhost:15672 | Queue dashboard |
| MinIO console | http://localhost:9001 | Object storage console |
| MinIO S3 API | http://localhost:9000 | S3-compatible endpoint |

---

## Testing & Build Verification

**Backend tests (pytest):**

```bash
# Inside the running backend container
docker compose exec backend python -m pytest backend/tests -q
```

If running locally outside Docker and imports fail, set `PYTHONPATH` to include the repo root and `backend/`:

```bash
PYTHONPATH="$PWD:$PWD/backend" python -m pytest backend/tests -q
```

**Frontend type-check + production build:**

```bash
# Via Docker (no local Node required)
docker compose build frontend

# Or locally
cd frontend && npm install && npm run build   # runs `tsc && vite build`
```

Continuous integration (`.github/workflows/ci.yml`) runs the backend pytest suite and the frontend TypeScript + Vite build on every push / pull request to `main`.

---

## AI Models & Git LFS

The AI model weights in `Ai_models/` (`violation_detection.pt`, `plate_detection.pt`) are **large binaries tracked with [Git LFS](https://git-lfs.com/)** (configured in `.gitattributes`). Because one weight file exceeds GitHub's 100 MB regular-file limit, Git LFS is required to clone the full repository:

```bash
git lfs install   # one-time setup
git lfs pull      # download the actual model weights
```

If you clone without Git LFS installed, the `.pt` files will be small pointer stubs and inference will not work until you run `git lfs pull`.

---

## Internal Naming Note

The **user-visible brand is ITVM** everywhere in the console (top bar, sidebar, login, case numbers, reports).

For backward compatibility with existing deployments and data volumes, several **internal infrastructure identifiers intentionally retain the legacy `stvis` name**, including:

- the PostgreSQL database name, user, and password defaults (`stvis`),
- RabbitMQ default credentials,
- the MinIO bucket name (`stvis-evidence`),
- Celery application names and the browser token storage key,
- the demo device token default.

These are environment-driven defaults — changing them would break existing local stacks and persisted volumes without any user-facing benefit, so they are deliberately preserved. Override them via `.env` if you need different values for a fresh deployment.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Frontend shows stale UI after a code change | Rebuild & restart: `docker compose up -d --build frontend` |
| `Ai_models/*.pt` are tiny / inference fails | Run `git lfs install && git lfs pull` |
| Backend unhealthy on first boot | Wait for postgres/rabbitmq/minio health checks; backend retries migrations |
| Can't log in | Confirm seeded credentials in `.env`; check the backend logs |
| CORS errors | Ensure `CORS_ORIGINS` / `FRONTEND_ORIGIN` match your frontend URL |

---

## License

This project is provided for academic and demonstration purposes. See the repository for any additional licensing terms.
