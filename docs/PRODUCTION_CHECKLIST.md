# Production Checklist — ITVM/STVIS

Use this checklist before deploying to any real environment.

---

## Security

- [ ] `SECRET_KEY` changed to a long random value (min 32 chars, use `openssl rand -hex 32`)
- [ ] `DEFAULT_ADMIN_PASSWORD` changed from `Admin@123456`
- [ ] `DEFAULT_SUPERVISOR_PASSWORD` changed from `Supervisor@123456`
- [ ] `MINIO_ROOT_PASSWORD` changed from `minioadmin`
- [ ] `RABBITMQ_DEFAULT_PASS` changed from `stvis`
- [ ] `DEMO_DEVICE_TOKEN` changed from `stvis-device-demo-token`
- [ ] `.env` is NOT committed to the repository
- [ ] HTTPS is configured via reverse proxy (nginx/Caddy)
- [ ] MinIO ports (9000/9001) are not publicly accessible without TLS + auth
- [ ] RabbitMQ management port (15672) is not publicly accessible

## Models

- [ ] `Ai_models/violation_detection.pt` exists (~115 MB)
- [ ] `Ai_models/plate_detection.pt` exists (~5 MB)
- [ ] `git lfs install && git lfs pull` has been run if using Git LFS

## Services

- [ ] `docker compose up -d --build` completes without errors
- [ ] `docker compose ps` shows all services healthy
- [ ] Backend API docs accessible: `http://<host>:8000/docs`
- [ ] Frontend accessible: `http://<host>:8080`
- [ ] MinIO console accessible: `http://<host>:9001`

## Functional Verification

- [ ] Log in as admin successfully
- [ ] Log in as supervisor successfully
- [ ] Upload a test image via the ingest API (see `docs/API_INGEST.md`)
- [ ] Confirm event appears in the backend logs within seconds
- [ ] Confirm case appears in the review queue
- [ ] Open the case and verify:
  - [ ] Annotated image is shown
  - [ ] Plate characters are displayed in slots
  - [ ] Violation name is shown
- [ ] Issue or reject the case
- [ ] Confirm audit log entry was created
- [ ] Export a report as CSV and confirm Arabic text is correct in Excel
- [ ] Verify health page shows all services as healthy

## Cleanup

- [ ] Remove any test cases from the DB if using a clean production instance
- [ ] Backup strategy for PostgreSQL data (`postgres-data` volume)
- [ ] Backup strategy for MinIO evidence (`minio-data` volume)
