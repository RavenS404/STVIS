# Device Ingest API — ITVM/STVIS

Roadside cameras and edge devices upload evidence to the STVIS backend using a simple authenticated HTTP multipart POST.

---

## Endpoint

```
POST http://<server>:8000/ingest/events
```

---

## Authentication

Authentication uses two custom headers sent with every request:

| Header | Description |
|--------|-------------|
| `X-Device-Code` | The device's unique code (e.g. `CAM-01`) |
| `X-Device-Token` | The device's secret token |

The backend validates both. If either is missing or incorrect, the request is rejected with **401 Unauthorized**.

---

## Request

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evidence` | file | ✅ Yes | Camera image (JPEG/PNG) |
| `captured_at` | datetime string | No | Timestamp of capture (ISO 8601). Defaults to server time if omitted |
| `external_ref` | string | No | External reference from the camera system |

---

## Response

```json
{
  "event_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "queued"
}
```

The `status` will be `queued` — inference happens asynchronously. The case will appear in the review queue after the worker processes the event.

---

## Examples

### PowerShell (Windows)

```powershell
curl.exe -X POST http://localhost:8000/ingest/events `
  -H "X-Device-Code: CAM-01" `
  -H "X-Device-Token: stvis-device-demo-token" `
  -F "evidence=@C:\path\to\image.jpg"
```

### curl (Linux/macOS)

```bash
curl -X POST http://localhost:8000/ingest/events \
  -H "X-Device-Code: CAM-01" \
  -H "X-Device-Token: stvis-device-demo-token" \
  -F "evidence=@/path/to/image.jpg"
```

### Python (requests)

```python
import requests

with open("image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/ingest/events",
        headers={
            "X-Device-Code": "CAM-01",
            "X-Device-Token": "stvis-device-demo-token",
        },
        files={"evidence": f},
    )
print(response.json())
```

### Bulk Upload (PowerShell script)

```powershell
.\scripts\bulk_ingest.ps1 -Folder .\test-images -Limit 10
```

---

## Seeded Demo Device

| Field | Value |
|-------|-------|
| Code | `CAM-01` |
| Token | `stvis-device-demo-token` |
| Name | بوابة الشمال |
| Location | تقاطع رئيسي |

---

## Adding More Devices

Admin users can register additional devices through the **Devices** page in the dashboard. After registration, the device code and generated token can be used with this same endpoint.
