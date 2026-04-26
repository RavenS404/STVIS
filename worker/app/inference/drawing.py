from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw


def crop_box(image: Image.Image, bbox: list[float] | tuple[float, float, float, float], *, padding: int = 4) -> Image.Image:
    x1, y1, x2, y2 = bbox
    x1 = max(int(x1) - padding, 0)
    y1 = max(int(y1) - padding, 0)
    x2 = min(int(x2) + padding, image.width)
    y2 = min(int(y2) + padding, image.height)
    return image.crop((x1, y1, x2, y2))


def annotate_event(image: Image.Image, detections: list[dict], case_overlays: list[dict]) -> bytes:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    palette = {
        "vehicle": "#0F4C81",
        "car windshield": "#0F4C81",
        "car_plate": "#C18A00",
        "using_mobile": "#A11B1B",
        "un seat-belt": "#A11B1B",
        "wrong_way": "#7B1FA2",
    }
    for item in detections:
        label = item["label"]
        bbox = item["bbox"]
        draw.rectangle(bbox, outline=palette.get(label, "#1F7A8C"), width=3)
        draw.text((bbox[0], max(bbox[1] - 16, 0)), f"{label} {item['confidence']:.2f}", fill=palette.get(label, "#1F7A8C"))

    for overlay in case_overlays:
        bbox = overlay["vehicle_bbox"]
        draw.rectangle(bbox, outline="#138A36", width=4)
        draw.text((bbox[0], bbox[1] + 4), overlay["case_number"], fill="#138A36")

    output = BytesIO()
    canvas.save(output, format="JPEG", quality=90)
    return output.getvalue()
