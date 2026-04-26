# ITVM/STVIS — Intelligent Traffic Violation Monitoring System
### نظام الرصد الذكي لمخالفات المرور

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![YOLO](https://img.shields.io/badge/YOLO-Ultralytics-FF6600?style=flat)](https://ultralytics.com/)

**ITVM/STVIS** is a production-style local-LAN intelligent traffic violation monitoring and issuance system built as a graduation project. It ingests evidence images from roadside cameras, runs AI inference to detect violations and read Egyptian Arabic license plates without OCR, and presents a full Arabic RTL supervisory dashboard for human review and decision-making.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [AI Models](#ai-models)
7. [Requirements](#requirements)
8. [Installation](#installation)
9. [Access URLs](#access-urls)
10. [Seeded Credentials](#seeded-credentials)
11. [Upload a Test Image](#upload-a-test-image)
12. [Tests](#tests)
13. [Development Workflow](#development-workflow)
14. [Clean Reset](#clean-reset)
15. [Production-Readiness Notes](#production-readiness-notes)
16. [Security Notes](#security-notes)
17. [Deployment Notes](#deployment-notes)
18. [Troubleshooting](#troubleshooting)
19. [Screenshots](#screenshots)
20. [License](#license)

---

## Overview

ITVM (Intelligent Traffic Violation Monitoring) / STVIS (Smart Traffic Violation Issuing System) provides:

- A **device ingest API** that accepts evidence images from roadside cameras via an authenticated token
- An **async Celery/RabbitMQ worker** that runs two YOLO models: one for violation detection, one for plate token recognition
- A **case management system** backed by PostgreSQL that stores events, vehicle cases, violations, plate reads, and evidence in MinIO
- A **React RTL web dashboard** that allows supervisors and admins to review cases, issue or reject violations, export reports, monitor health, and manage the system

---

## Features

| Area | Capability |
|------|-----------|
| 🚦 **Violation Detection** | YOLO model detects: vehicle, car windshield, un-fastened seat belt, using mobile, wrong way |
| 🪪 **Plate Reading** | YOLO plate-token model reads Egyptian Arabic plates directly — **no OCR** |
| 🇦🇪 **Arabic RTL UI** | Full right-to-left React dashboard with Arabic labels |
| 📋 **Review Queue** | Supervisors see only cases that require manual review; debounced search |
| 📁 **Case Details** | Annotated evidence image, Egyptian-style plate display with individual character slots, issue/reject/escalate controls, prev/next navigation |
| 📊 **Reports** | CSV export with UTF-8 BOM (Arabic-safe in Excel) |
| 🔒 **RBAC** | Admin and Supervisor roles; backend-enforced on every decision endpoint |
| 🔍 **Audit Logs** | Full immutable audit trail for every action |
| ⚙️ **Settings** | DB-backed thresholds (confidence, auto-issue, association parameters) |
| 🏥 **Health Monitor** | Real-time health cards for all services |
| 🐳 **Docker Compose** | One-command local deployment, fully self-contained |

---

## System Architecture

```
Roadside Camera (or test script)
        │
        ▼
POST /ingest/events  ──►  FastAPI validates device token
        │                        │
        │                        ▼
        │                 PostgreSQL stores Event + InferenceRun
        │                        │
        ▼                        ▼
MinIO stores evidence ◄── Backend uploads original image
                                 │
                                 ▼
                        RabbitMQ queues inference job
                                 │
                                 ▼
                         Celery Worker
                           ├─ YOLO violation model → detect vehicles/violations/plates
                           ├─ YOLO plate token model → detect Arabic character tokens
                           ├─ Association engine  → link plates/violations to vehicles
                           ├─ Policy engine        → determine review state
                           └─ MinIO stores annotated + crop images
                                 │
                                 ▼
                        PostgreSQL stores VehicleCase + ViolationRecord + PlateRead
                                 │
                                 ▼
              React RTL Dashboard ──► Supervisor reviews case
                                        ├─ Issue violation
                                        ├─ Reject case
                                        └─ Escalate to admin
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + TypeScript + Vite | Arabic RTL SPA dashboard |
| Backend API | FastAPI + Pydantic v2 | REST API, auth, business logic |
| Worker | Celery + Ultralytics YOLO | Async AI inference pipeline |
| Database | PostgreSQL 16 | Cases, events, users, settings, audit |
| Object Storage | MinIO | Evidence images, crops, annotated frames |
| Message Broker | RabbitMQ 3.13 | Task queue between API and worker |
| AI | PyTorch + Ultralytics | Violation detection + plate token detection |
| Deployment | Docker Compose | Fully containerized local deployment |

---

## Project Structure

```
STVIS/
├── backend/               FastAPI application
│   ├── app/
│   │   ├── api/           Route handlers (cases, ingest, admin, etc.)
│   │   ├── core/          Config, security, auth
│   │   ├── db/            Session, seed data
│   │   ├── models/        SQLAlchemy ORM models
│   │   ├── schemas/       Pydantic request/response schemas
│   │   └── services/      Business logic (case, ingest, health, etc.)
│   └── tests/             pytest test suite (18+ tests)
│
├── worker/                Celery inference worker
│   └── app/
│       ├── inference/     Model runtime + drawing utilities
│       └── tasks.py       Main Celery task (process_event)
│
├── common/                Shared Python code
│   ├── constants/         Enums, plate mapping, violation catalog, settings
│   └── utils/             plate_reading, association, policy engines
│
├── frontend/              React + TypeScript SPA
│   └── src/
│       ├── app/           Types, routing, global CSS, presentation helpers
│       ├── components/    Shared UI components
│       ├── pages/         Page components (Dashboard, Review, History, etc.)
│       ├── services/      API client functions
│       └── hooks/         Custom React hooks (auth, etc.)
│
├── Ai_models/             YOLO model weights (tracked by Git LFS)
│   ├── violation_detection.pt   (~115 MB)
│   └── plate_detection.pt       (~5 MB)
│
├── infra/docker/          Dockerfiles for each service
├── scripts/               Helper scripts (bulk_ingest.ps1, etc.)
├── docs/                  Additional documentation
├── docker-compose.yml     Production Docker Compose
├── docker-compose.dev.yml Hot-reload dev overrides
└── .env.example           Environment template (copy to .env)
```

---

## AI Models

### `Ai_models/violation_detection.pt` (~115 MB)

Detects traffic-related objects in camera frames:

| Class ID | Label | Notes |
|---------|-------|-------|
| 0 | car windshield | Support zone for seat-belt violations |
| 1 | car_plate | Plate bounding box |
| 2 | seat-belt | Fastened seat belt |
| 3 | un seat-belt | **Violation**: unfastened seat belt |
| 4 | using_mobile | **Violation**: mobile phone use |
| 5 | vehicle | Vehicle bounding box |
| 6 | wrong_way | **Violation**: wrong-way driving |

### `Ai_models/plate_detection.pt` (~5 MB)

Reads Egyptian Arabic license plates by detecting **individual character tokens** directly. No OCR is used.

- Detects digits: `1–9`
- Detects Arabic letter tokens: `alf`, `ba2`, `dal`, `ein`, `fa2`, `gem`, `ha2`, `lam`, `mem`, `non`, `qaf`, `ra2`, `sad`, `sen`, `ta2`, `waw`, `ya2`
- Class-to-Arabic mapping: `common/constants/plate_mapping.py`
- Reading + reconstruction logic: `common/utils/plate_reading.py`

> **Model files are tracked with Git LFS.** After cloning, run `git lfs pull` to download them.

---

## Requirements

> Python, Node.js, PostgreSQL, RabbitMQ, and MinIO do **not** need to be installed locally. Docker handles all services.

- [Git](https://git-scm.com/)
- [Git LFS](https://git-lfs.github.com/) — for model weights
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Docker Compose)
- A modern web browser

---

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/RavenS404/STVIS.git
cd STVIS

# 2. Pull model files via Git LFS
git lfs install
git lfs pull

# 3. Create your local environment file
Copy-Item .env.example .env
# Edit .env if needed (change passwords for real deployments)

# 4. Build and start all services
docker compose up -d --build
```

Wait about 30–60 seconds for all services to become healthy, then open:

---

## Access URLs

| Service | URL |
|---------|-----|
| 🖥️ Frontend Dashboard | http://localhost:8080 |
| 📖 Backend API Docs | http://localhost:8000/docs |
| 🐰 RabbitMQ Management | http://localhost:15672 |
| 🗄️ MinIO Console | http://localhost:9001 |

---

## Seeded Credentials

> These are seeded automatically on first startup from `.env.example` defaults.

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123456` |
| Supervisor | `supervisor` | `Supervisor@123456` |

**Demo device:**

| Field | Value |
|-------|-------|
| Device Code | `CAM-01` |
| Device Token | `stvis-device-demo-token` |

---

## Upload a Test Image

The ingest endpoint accepts authenticated POST requests from edge devices:

```
POST http://localhost:8000/ingest/events
```

**Headers:**

| Header | Value |
|--------|-------|
| `X-Device-Code` | `CAM-01` |
| `X-Device-Token` | `stvis-device-demo-token` |

**Form field:** `evidence` (image file, multipart/form-data)

**PowerShell example:**

```powershell
curl.exe -X POST http://localhost:8000/ingest/events `
  -H "X-Device-Code: CAM-01" `
  -H "X-Device-Token: stvis-device-demo-token" `
  -F "evidence=@C:\path\to\your\image.jpg"
```

**Bulk upload (test-images folder):**

```powershell
.\scripts\bulk_ingest.ps1 -Folder .\test-images -Limit 10
```

After uploading, check the **Review Queue** tab in the dashboard — processed cases appear there within a few seconds.

---

## Tests

**Backend (pytest):**

```powershell
$env:PYTHONPATH = "$PWD;$PWD\backend"
python -m pytest backend\tests -v
```

> 18+ tests covering RBAC, security, policy engine, and association service.

**Frontend (TypeScript + build):**

```powershell
cd frontend
npm install
npm run build
```

---

## Development Workflow

Use `docker-compose.dev.yml` overrides for hot-reloading without full rebuilds:

```powershell
# First time: build images
docker compose build backend worker

# Start dev stack (hot-reload for backend + worker + frontend Vite dev server)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d `
  postgres rabbitmq minio minio-init backend worker frontend-dev
```

- **Backend**: runs with `uvicorn --reload` → code changes apply immediately
- **Worker**: bind-mounted source; restart after worker changes:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart worker
```

- **Frontend dev**: `http://localhost:8080` (Vite)

---

## Clean Reset

> ⚠️ This deletes all database data, MinIO evidence, and RabbitMQ state.

```powershell
docker compose down -v --remove-orphans
docker compose up -d --build
```

---

## Production-Readiness Notes

This project includes several production-quality engineering decisions:

- **RBAC enforcement**: `case_decision` endpoint is protected at the backend level; frontend button hiding alone is not relied on
- **SECRET_KEY hard fail**: in `ENVIRONMENT=production`, a missing or default secret key raises a `RuntimeError` at startup
- **Sanitized health errors**: internal service details (URLs, passwords) are never leaked to API clients
- **Sanitized image errors**: ingestion errors return safe messages to clients; full details are server-side only
- **DB-backed thresholds**: confidence and association thresholds are stored in `SystemSetting` and read from the DB, not hardcoded
- **Optimized API read path**: `reconstruct_plate()` is not called on every case list request
- **UTF-8 BOM CSV export**: the frontend prepends `\uFEFF` so Excel renders Arabic text correctly without garbling
- **Search debounce**: `ReviewQueuePage` uses `useDeferredValue` (300ms) to avoid API floods on keystroke
- **`no_violation` state**: cases with no actionable violation are assigned `no_violation` state and excluded from the supervisor review queue automatically

---

## Security Notes

- **Never commit `.env`** — only `.env.example` belongs in the repo
- **Change `SECRET_KEY`** to a long random value before any real deployment
- **Change all default passwords** (DB, MinIO, RabbitMQ, admin users, device token) in production
- **Do not expose MinIO ports** (9000/9001) publicly without authentication and TLS
- **Device tokens must be protected** — treat them like API keys
- **Use HTTPS in production** — add a reverse proxy (nginx, Caddy) with TLS termination

---

## Deployment Notes

- GitHub cannot natively host or run this full Docker stack.
- **For a real deployment**: provision a VPS or cloud VM and use Docker Compose or convert to Kubernetes.
- **For CI**: GitHub Actions can run the backend tests and frontend build (see `.github/workflows/ci.yml`).
- **For development**: GitHub Codespaces can be used with Docker-in-Docker or devcontainers.

### Recommended GitHub repo description

> Production-style local LAN system for intelligent traffic violation monitoring using FastAPI, React, PostgreSQL, RabbitMQ, MinIO, Celery, and YOLO.

### Suggested GitHub topics

`fastapi` · `react` · `postgresql` · `celery` · `rabbitmq` · `minio` · `yolo` · `computer-vision` · `traffic-violation` · `arabic-rtl` · `docker-compose` · `graduation-project`

### Rename the repository (optional)

GitHub → Settings → General → Repository name → `ITVM-STVIS` (or your preferred name)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Docker not running | Start Docker Desktop first |
| Port already in use | `netstat -ano \| findstr :8080` → kill the process using that port |
| Models missing (`FileNotFoundError`) | Run `git lfs install && git lfs pull` |
| Worker stuck / not processing | Check `docker compose logs worker`; restart with `docker compose restart worker` |
| Images not loading in UI | Check MinIO is healthy: `docker compose ps` |
| Arabic CSV garbled in Excel | Use the export button in Reports — it adds UTF-8 BOM automatically |
| RabbitMQ login fails | Check `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS` in `.env` match values in compose |
| Need a clean slate | `docker compose down -v --remove-orphans && docker compose up -d --build` |

---

## Screenshots

> Add screenshots to `docs/screenshots/` and update the paths below.

| Screen | File |
|--------|------|
| Login | `docs/screenshots/login.png` |
| Dashboard | `docs/screenshots/dashboard.png` |
| Review Queue | `docs/screenshots/review-queue.png` |
| Case Details | `docs/screenshots/case-details.png` |
| Reports | `docs/screenshots/reports.png` |
| Health Monitor | `docs/screenshots/health.png` |

---

## License

Add your chosen license before public release.

Suggested options: MIT, Apache 2.0, or a custom academic/graduation project license.

To add: create a `LICENSE` file in the repository root.

---

*Built as a Computer Engineering graduation project — ITVM/STVIS, 2025.*
