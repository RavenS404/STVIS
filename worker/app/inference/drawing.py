from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw


def _box_area(bbox: list[float] | tuple[float, float, float, float]) -> float:
    return max(float(bbox[2]) - float(bbox[0]), 0.0) * max(float(bbox[3]) - float(bbox[1]), 0.0)


def _intersection_over_union(
    first: list[float] | tuple[float, float, float, float],
    second: list[float] | tuple[float, float, float, float],
) -> float:
    x1 = max(float(first[0]), float(second[0]))
    y1 = max(float(first[1]), float(second[1]))
    x2 = min(float(first[2]), float(second[2]))
    y2 = min(float(first[3]), float(second[3]))
    intersection = _box_area((x1, y1, x2, y2))
    union = _box_area(first) + _box_area(second) - intersection
    return intersection / union if union > 0 else 0.0


def _is_same_annotation_spot(
    first: list[float] | tuple[float, float, float, float],
    second: list[float] | tuple[float, float, float, float],
) -> bool:
    return _intersection_over_union(first, second) >= 0.92


def _deduplicate_detections(detections: list[dict]) -> list[dict]:
    deduplicated: list[dict] = []
    for item in sorted(detections, key=lambda detection: detection.get("confidence") or 0, reverse=True):
        bbox = item["bbox"]
        if any(_is_same_annotation_spot(bbox, existing["bbox"]) for existing in deduplicated):
            continue
        deduplicated.append(item)
    return deduplicated


def _deduplicate_case_overlays(case_overlays: list[dict]) -> list[dict]:
    deduplicated: list[dict] = []
    for overlay in case_overlays:
        bbox = overlay["vehicle_bbox"]
        if any(_is_same_annotation_spot(bbox, existing["vehicle_bbox"]) for existing in deduplicated):
            continue
        deduplicated.append(overlay)
    return deduplicated


def crop_box(image: Image.Image, bbox: list[float] | tuple[float, float, float, float], *, padding: int = 4) -> Image.Image:
    x1, y1, x2, y2 = bbox
    x1 = max(int(x1) - padding, 0)
    y1 = max(int(y1) - padding, 0)
    x2 = min(int(x2) + padding, image.width)
    y2 = min(int(y2) + padding, image.height)
    return image.crop((x1, y1, x2, y2))


def _padded_bbox(
    image: Image.Image,
    bbox: list[float] | tuple[float, float, float, float],
    *,
    padding_ratio: float,
    min_padding: int = 8,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = [float(value) for value in bbox]
    width = max(x2 - x1, 1.0)
    height = max(y2 - y1, 1.0)
    pad_x = max(int(width * padding_ratio), min_padding)
    pad_y = max(int(height * padding_ratio), min_padding)
    return (
        max(int(x1) - pad_x, 0),
        max(int(y1) - pad_y, 0),
        min(int(x2) + pad_x, image.width),
        min(int(y2) + pad_y, image.height),
    )


def _union_bbox(items: list[list[float] | tuple[float, float, float, float]]) -> tuple[float, float, float, float] | None:
    if not items:
        return None
    return (
        min(float(item[0]) for item in items),
        min(float(item[1]) for item in items),
        max(float(item[2]) for item in items),
        max(float(item[3]) for item in items),
    )


def annotate_violations_only(image: Image.Image, violations: list[dict]) -> bytes:
    canvas = image.copy()
    draw = ImageDraw.Draw(canvas)
    palette = {
        "using_mobile": "#A11B1B",
        "un seat-belt": "#A11B1B",
        "wrong_way": "#7B1FA2",
    }
    for item in _deduplicate_detections(violations):
        label = item["label"]
        bbox = item["bbox"]
        color = palette.get(label, "#A11B1B")
        draw.rectangle(bbox, outline=color, width=4)
        draw.text((bbox[0], max(bbox[1] - 18, 0)), f"{label} {item['confidence']:.2f}", fill=color)

    output = BytesIO()
    canvas.save(output, format="JPEG", quality=92)
    return output.getvalue()


def crop_driver_zoom(
    image: Image.Image,
    *,
    support_bbox: list[float] | tuple[float, float, float, float] | None,
    vehicle_bbox: list[float] | tuple[float, float, float, float],
    violation_bboxes: list[list[float] | tuple[float, float, float, float]],
) -> Image.Image:
    focus_bbox = support_bbox or _union_bbox(violation_bboxes)
    if focus_bbox is None:
        x1, y1, x2, y2 = [float(value) for value in vehicle_bbox]
        focus_bbox = (x1, y1, x2, y1 + ((y2 - y1) * 0.58))

    crop_bounds = _padded_bbox(image, focus_bbox, padding_ratio=0.38, min_padding=14)
    zoom = image.crop(crop_bounds)
    min_width = 520
    if zoom.width < min_width:
        scale = min_width / max(zoom.width, 1)
        zoom = zoom.resize((int(zoom.width * scale), int(zoom.height * scale)), Image.Resampling.LANCZOS)
    return zoom


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
    cleaned_case_overlays = _deduplicate_case_overlays(case_overlays)
    cleaned_detections = [
        item
        for item in _deduplicate_detections(detections)
        if not any(_is_same_annotation_spot(item["bbox"], overlay["vehicle_bbox"]) for overlay in cleaned_case_overlays)
    ]

    for item in cleaned_detections:
        label = item["label"]
        bbox = item["bbox"]
        draw.rectangle(bbox, outline=palette.get(label, "#1F7A8C"), width=3)
        draw.text((bbox[0], max(bbox[1] - 16, 0)), f"{label} {item['confidence']:.2f}", fill=palette.get(label, "#1F7A8C"))

    for overlay in cleaned_case_overlays:
        bbox = overlay["vehicle_bbox"]
        draw.rectangle(bbox, outline="#138A36", width=4)
        draw.text((bbox[0], bbox[1] + 4), overlay["case_number"], fill="#138A36")

    output = BytesIO()
    canvas.save(output, format="JPEG", quality=90)
    return output.getvalue()
