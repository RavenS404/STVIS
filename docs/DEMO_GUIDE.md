# Demo Guide — ITVM/STVIS

A step-by-step walkthrough for demonstrating the system in a graduation presentation.

---

## Prerequisites

System must be running:

```powershell
docker compose up -d --build
```

Wait ~60 seconds for all services to become healthy.

---

## Step 1 — Login

Open http://localhost:8080

Log in with:
- Username: `admin`
- Password: `Admin@123456`

> **Talking point:** The system uses Role-Based Access Control (RBAC). The Admin role has full access. The Supervisor role can review cases and issue violations but cannot manage users or devices.

---

## Step 2 — Dashboard Overview

The main dashboard shows:
- Total cases processed
- Breakdown by review state
- Cases requiring supervisor review (queue depth)
- Recent cases

> **Talking point:** All labels, buttons, and content are in Arabic with full right-to-left layout support.

---

## Step 3 — Upload a Test Image

Open a PowerShell terminal and run:

```powershell
curl.exe -X POST http://localhost:8000/ingest/events `
  -H "X-Device-Code: CAM-01" `
  -H "X-Device-Token: stvis-device-demo-token" `
  -F "evidence=@.\test-images\<your-image.jpg>"
```

Or use the bulk script:

```powershell
.\scripts\bulk_ingest.ps1 -Folder .\test-images -Limit 3
```

> **Talking point:** In production, roadside cameras call this API automatically. The API authenticates the device by code and secret token before accepting any image.

---

## Step 4 — Watch Case Processing

Refresh the Dashboard or go to **السجل (History)**.

Within a few seconds, a new case should appear.

You can also watch the worker logs:

```powershell
docker compose logs -f worker
```

> **Talking point:** The YOLO violation model detects vehicles, seat belts, and phone use. The plate model reads Egyptian Arabic plates without any OCR — it detects individual character tokens directly.

---

## Step 5 — Review Queue

Click **طابور المراجعة** (Review Queue) in the sidebar.

Cases that require human review appear here.

> **Talking point:** The policy engine automatically decides whether a case can be auto-issued or needs a supervisor. Clean cases (no actionable violation) are excluded from this queue entirely.

---

## Step 6 — Case Details

Click on a case to open the Case Details page.

Point out:
- **Annotated image** with detection bounding boxes
- **Egyptian plate display** showing each letter and digit in a separate slot
- **Violation name** in Arabic
- **Status badge** showing the current review state
- **Previous/Next** navigation buttons for efficient review

> **Talking point:** The plate reading separates letters from digits visually and shows each character individually — making it easy for a supervisor to verify or correct the reading.

---

## Step 7 — Issue or Reject

Use the action buttons:
- **إصدار** (Issue) — confirms the violation
- **رفض** (Reject) — closes the case as invalid
- **تصعيد لمشرف** (Escalate to supervisor) — sends to senior review

After acting, the system auto-navigates to the next review case.

> **Talking point:** Every action is backed by backend RBAC. Hiding a button on the frontend is not enough — the server enforces permissions.

---

## Step 8 — Reports

Click **التقارير** (Reports) in the sidebar.

Download a CSV report and open it in Excel.

> **Talking point:** The CSV uses UTF-8 BOM encoding so Arabic text renders correctly in Excel without any manual configuration.

---

## Step 9 — Health Monitor

Click **الصحة** (Health) in the sidebar.

The page shows the real-time status of:
- Database
- Message broker
- Storage
- Worker queue

> **Talking point:** Error details (URLs, passwords, internal stack traces) are never leaked to the client — only safe status summaries are shown.

---

## Step 10 — Audit Log

Click **التدقيق** (Audit) in the sidebar.

Every action (decision, login, setting change) is permanently recorded.

---

## Step 11 — Settings (Admin Only)

Click **الإعدادات** (Settings) in the sidebar.

The operator can adjust:
- Minimum confidence thresholds for violations and plate reads
- Association parameters
- Auto-issue policy

> **Talking point:** All configuration is stored in the database — no code changes required to tune the system.
