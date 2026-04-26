# Setup Guide — ITVM/STVIS

## Prerequisites

| Tool | Purpose | Download |
|------|---------|---------|
| Git | Version control | https://git-scm.com |
| Git LFS | Model file downloads | https://git-lfs.github.com |
| Docker Desktop | Runs all services | https://www.docker.com/products/docker-desktop |

> **Python, Node.js, PostgreSQL, RabbitMQ, and MinIO are not needed locally** — Docker handles everything.

---

## Step 1 — Clone Repository

```powershell
git clone https://github.com/RavenS404/STVIS.git
cd STVIS
```

---

## Step 2 — Download Model Files (Git LFS)

The two YOLO model files are tracked by Git LFS:

```powershell
git lfs install
git lfs pull
```

Verify they exist:

```powershell
Get-ChildItem Ai_models\
# Expected: plate_detection.pt (~5 MB), violation_detection.pt (~115 MB)
```

If models are missing after `git lfs pull`, see [Troubleshooting](#troubleshooting).

---

## Step 3 — Configure Environment

```powershell
Copy-Item .env.example .env
```

For local testing, the defaults in `.env.example` work without changes.

**For non-local or production deployments:**

Edit `.env` and change:

```
SECRET_KEY=<long-random-string>
MINIO_ROOT_PASSWORD=<strong-password>
RABBITMQ_DEFAULT_PASS=<strong-password>
DEFAULT_ADMIN_PASSWORD=<strong-password>
DEFAULT_SUPERVISOR_PASSWORD=<strong-password>
DEMO_DEVICE_TOKEN=<strong-token>
```

---

## Step 4 — Start All Services

```powershell
docker compose up -d --build
```

This will:
1. Pull base images (postgres, rabbitmq, minio)
2. Build backend, worker, and frontend images
3. Start all containers
4. Run database migrations and seed data on backend startup
5. Create the MinIO bucket automatically

**Wait ~30–60 seconds** for all health checks to pass.

Check service status:

```powershell
docker compose ps
```

All services should show `healthy` or `running`.

---

## Step 5 — Verify

Open http://localhost:8080 and log in with:
- Username: `admin`
- Password: `Admin@123456`

Open http://localhost:8000/docs to verify the API is running.

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `git lfs pull` fails | Ensure Git LFS is installed: `git lfs version` |
| Models missing | Download `.pt` files and place them in `Ai_models/` manually |
| Port conflicts | Edit `.env` to change mapped ports, or stop conflicting processes |
| Database seed fails | Run `docker compose down -v` then `docker compose up -d --build` |
| Backend won't start | Check `docker compose logs backend` for details |
| Worker not processing | Check `docker compose logs worker`; ensure models exist |
| Images not showing | Check `docker compose logs minio`; verify `MINIO_BUCKET` in `.env` |
