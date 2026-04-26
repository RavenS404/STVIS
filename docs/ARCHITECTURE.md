# Architecture — ITVM/STVIS

## Services Overview

| Service | Technology | Responsibility |
|---------|-----------|---------------|
| `backend` | FastAPI | REST API, auth, device ingestion, case management |
| `worker` | Celery + YOLO | Async AI inference, plate reading, policy evaluation |
| `postgres` | PostgreSQL 16 | Persistent storage for all domain data |
| `minio` | MinIO | Object storage for all evidence images and crops |
| `rabbitmq` | RabbitMQ 3.13 | Message broker between backend and worker |
| `frontend` | React (served by nginx) | Arabic RTL web dashboard |

---

## Data Flow

### 1. Device Ingest

```
Camera Device
  └─► POST /ingest/events
      Headers: X-Device-Code, X-Device-Token
      Field: evidence (image file)
            │
            ▼
      authenticate_device()
      ├─ Verify X-Device-Code exists and is active
      └─ Verify X-Device-Token (constant-time HMAC compare)
            │
            ▼
      IngestEventService.ingest_device_event()
      ├─ Upload image to MinIO (kind=original)
      ├─ Create Event record in PostgreSQL
      └─ Create InferenceRun record (QUEUED)
            │
            ▼
      Dispatch Celery task → RabbitMQ
```

### 2. Worker Inference Pipeline

```
Celery Worker receives task(event_id, run_id)
      │
      ▼
Load YOLO models if not already cached (LRU cache)
      │
      ▼
Run violation_detection.pt on original image
  → Detected: vehicles, windshields, plates, violations
      │
      ▼
Run plate_detection.pt on plate crop(s)
  → Detected: individual Arabic plate token characters
      │
      ▼
Association Engine (common/utils/association.py)
  → Link plates → vehicles
  → Link violations → vehicles
  → Score ambiguity for each association
      │
      ▼
For each vehicle association:
  ├─ PlateReadingEngine → ordered Arabic tokens → letters_ar + digits_ar
  └─ PolicyEngine → evaluate thresholds, assign review_state
      │
      ▼
Write to PostgreSQL:
  ├─ VehicleCase (one per detected vehicle)
  ├─ CasePlateRead (Arabic letter/digit display)
  └─ CaseViolationRecord (one per actionable violation)
      │
      ▼
Upload annotated image + crops to MinIO
```

### 3. Supervisor Review

```
React Dashboard (polling / manual refresh)
  └─► GET /cases?only_supervisor_queue=true
      │
      ▼
  Supervisor selects a case → GET /cases/{id}
      ├─ Loads assets (annotated image, plate crop)
      ├─ Displays Egyptian-style plate preview
      └─ Displays violations with confidence
            │
            ▼
  Supervisor action → POST /cases/{id}/decision
  { decision: "issue" | "reject" | "send_to_supervisor" }
      │
      ├─ RBAC check (SUPERVISOR or ADMIN required)
      ▼
  Update CaseReviewState + write AuditLog entry
```

---

## Case Lifecycle

```
CREATED
  │
  ▼
policy evaluates: does case have an actionable violation?
  │
  ├─ No violation detected → NO_VIOLATION (excluded from queue)
  │
  └─ Violation detected:
      ├─ Confidence above direct-issue threshold + auto_issue_enabled → ISSUED (system)
      ├─ Confidence requires human review → SUPERVISOR_REVIEW_REQUIRED
      └─ Issue-ready, waiting for manual confirmation → DIRECT_ISSUE_READY
                │
                ▼
         Supervisor reviews
                │
         ├─ Issue → ISSUED (human)
         ├─ Reject → REJECTED
         └─ Escalate → SUPERVISOR_REVIEW_REQUIRED (stays queued)
```

---

## Roles

| Role | Permissions |
|------|------------|
| `ADMIN` | Everything: users, devices, settings, all decisions |
| `SUPERVISOR` | Review queue, case decisions, reports, health — cannot manage users or devices |

---

## Storage Layout (MinIO)

All assets stored in bucket `stvis-evidence` (default):

| `kind` | Description |
|--------|-------------|
| `original` | Raw uploaded camera image |
| `annotated_event` | Image with YOLO bounding boxes drawn |
| `vehicle_crop` | Cropped vehicle region |
| `plate_crop` | Cropped plate region |
| `annotated_case` | Case-level annotated composite |
