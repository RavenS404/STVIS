from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import median
from typing import Iterable, Sequence

from common.constants.plate_mapping import (
    ARABIC_MAP,
    DIGIT_CLASSES,
    IGNORED_CLASSES,
    LETTER_CLASSES,
    PLATE_CLASS_ALIASES,
)

# ── Confidence thresholds ────────────────────────────────────────────
DEFAULT_CHAR_CONF_THRESHOLD = 0.55   # tokens below this are discarded
MIN_PLATE_CONF_FOR_DISPLAY = 0.30    # plate avg below → "unclear"
MIN_TOKEN_COUNT = 3                  # fewer surviving tokens → "unclear"

# ── IoU threshold for deduplication ──────────────────────────────────
IOU_DEDUP_THRESHOLD = 0.45


@dataclass(slots=True)
class PlateToken:
    raw_label: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def normalized_label(self) -> str:
        return PLATE_CLASS_ALIASES.get(self.raw_label, self.raw_label)

    @property
    def arabic_value(self) -> str:
        label = self.normalized_label
        if label in ARABIC_MAP:
            return ARABIC_MAP[label]
        if label in IGNORED_CLASSES:
            return ""
        return "UNKNOWN_CLASS"

    @property
    def char_type(self) -> str:
        """Return 'digit', 'letter', or 'unknown'."""
        label = self.normalized_label
        if label in DIGIT_CLASSES:
            return "digit"
        if label in LETTER_CLASSES:
            return "letter"
        return "unknown"

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def is_digit(self) -> bool:
        return self.char_type == "digit"

    @property
    def is_letter(self) -> bool:
        return self.char_type == "letter"


@dataclass(slots=True)
class PlateReadResult:
    raw_text_visual: str
    arabic_text_display: str
    display_summary_ar: str
    normalized_search_value: str
    letters_ar: str
    digits_ar: str
    raw_letters: str
    raw_digits: str
    plate_confidence: float
    token_count: int
    row_count: int
    token_details: list[dict]


# ── Token construction ───────────────────────────────────────────────

def build_tokens(detections: Iterable[dict]) -> list[PlateToken]:
    tokens: list[PlateToken] = []
    for item in detections:
        bbox = item["bbox"]
        tokens.append(
            PlateToken(
                raw_label=str(item["label"]),
                confidence=float(item["confidence"]),
                x1=float(bbox[0]),
                y1=float(bbox[1]),
                x2=float(bbox[2]),
                y2=float(bbox[3]),
            )
        )
    return tokens


# ── Filtering ────────────────────────────────────────────────────────

def _token_iou(a: PlateToken, b: PlateToken) -> float:
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    intersection = (x2 - x1) * (y2 - y1)
    union = (a.width * a.height) + (b.width * b.height) - intersection
    return intersection / max(union, 1.0)


def _estimate_canvas(tokens: Sequence[PlateToken]) -> tuple[float, float]:
    width = max((token.x2 for token in tokens), default=1.0)
    height = max((token.y2 for token in tokens), default=1.0)
    return max(width, 1.0), max(height, 1.0)


def _filter_tokens(
    tokens: Sequence[PlateToken],
    *,
    conf_threshold: float = DEFAULT_CHAR_CONF_THRESHOLD,
) -> list[PlateToken]:
    """Filter out noise, ignored classes, and banner-sized false positives."""
    if not tokens:
        return []
    canvas_width, canvas_height = _estimate_canvas(tokens)
    filtered: list[PlateToken] = []
    for token in tokens:
        # Skip below confidence threshold
        if token.confidence < conf_threshold:
            continue
        # Skip ignored/unknown classes
        if token.char_type == "unknown":
            continue
        # Skip banner-sized boxes (full-image false positive)
        width_ratio = token.width / canvas_width
        height_ratio = token.height / canvas_height
        area_ratio = width_ratio * height_ratio
        if width_ratio > 0.42 or height_ratio > 0.82 or area_ratio > 0.18:
            continue
        filtered.append(token)
    return filtered


def _deduplicate_tokens(tokens: Sequence[PlateToken]) -> list[PlateToken]:
    """Remove overlapping detections, keeping highest confidence."""
    deduplicated: list[PlateToken] = []
    for token in sorted(tokens, key=lambda item: item.confidence, reverse=True):
        if any(_token_iou(token, existing) >= IOU_DEDUP_THRESHOLD for existing in deduplicated):
            continue
        deduplicated.append(token)
    return sorted(deduplicated, key=lambda item: (item.center_y, item.center_x))


# ── Row clustering ───────────────────────────────────────────────────

def _cluster_rows(tokens: Sequence[PlateToken]) -> list[list[PlateToken]]:
    if not tokens:
        return []

    heights = [max(token.height, 1.0) for token in tokens]
    tolerance = max(median(heights) * 0.55, 8.0)
    rows: list[dict] = []

    for token in sorted(tokens, key=lambda item: item.center_y):
        placed = False
        for row in rows:
            if abs(token.center_y - row["mean_y"]) <= tolerance:
                row["tokens"].append(token)
                row["mean_y"] = sum(item.center_y for item in row["tokens"]) / len(row["tokens"])
                placed = True
                break
        if not placed:
            rows.append({"mean_y": token.center_y, "tokens": [token]})

    return [row["tokens"] for row in sorted(rows, key=lambda item: item["mean_y"])]


def _row_quality(row: Sequence[PlateToken]) -> float:
    confidences = [token.confidence for token in row]
    return round((max(confidences) * 0.65) + (median(confidences) * 0.35), 4)


def _select_signal_rows(rows: Sequence[list[PlateToken]]) -> list[list[PlateToken]]:
    if not rows:
        return []
    scored_rows = [(row, _row_quality(row)) for row in rows]
    best_score = max(score for _row, score in scored_rows)
    selected = [row for row, score in scored_rows if score >= max(0.16, best_score * 0.42)]
    return selected or [max(scored_rows, key=lambda item: item[1])[0]]


# ── Sorting: Egyptian plate convention ───────────────────────────────
#
# Egyptian plates visually show:   LETTERS  DIGITS   (from right)
# In RTL display we produce:      letters_part + space + digits_part
# Each group is internally sorted by x_center (left-to-right visual).

def _sort_row_egyptian(row: Sequence[PlateToken]) -> tuple[list[PlateToken], list[PlateToken]]:
    """Sort one row into (letters_sorted, digits_sorted) by x_center."""
    letters = sorted([t for t in row if t.is_letter], key=lambda t: t.center_x)
    digits = sorted([t for t in row if t.is_digit], key=lambda t: t.center_x)
    return letters, digits


def _join_arabic(tokens: Sequence[PlateToken]) -> str:
    return " ".join(token.arabic_value for token in tokens if token.arabic_value)


def _join_raw(tokens: Sequence[PlateToken]) -> str:
    return " ".join(token.normalized_label for token in tokens)


# ── Main reconstruction entry point ─────────────────────────────────

def reconstruct_plate(
    detections: Iterable[dict],
    *,
    conf_threshold: float = DEFAULT_CHAR_CONF_THRESHOLD,
) -> PlateReadResult:
    tokens = build_tokens(detections)
    filtered_tokens = _deduplicate_tokens(_filter_tokens(tokens, conf_threshold=conf_threshold))
    rows = _select_signal_rows(_cluster_rows(filtered_tokens))

    raw_visual_rows: list[str] = []
    display_rows: list[str] = []
    ordered_tokens: list[dict] = []
    letters_flat: list[PlateToken] = []
    digits_flat: list[PlateToken] = []

    for row_index, row in enumerate(rows):
        letters_sorted, digits_sorted = _sort_row_egyptian(row)
        visual = sorted(row, key=lambda item: item.center_x)

        # Egyptian display: letters then digits
        display = letters_sorted + digits_sorted
        raw_visual_rows.append(_join_raw(visual))
        display_rows.append(_join_arabic(display))
        letters_flat.extend(letters_sorted)
        digits_flat.extend(digits_sorted)

        for visual_index, token in enumerate(visual):
            ordered_tokens.append(
                {
                    "row_index": row_index,
                    "visual_index": visual_index,
                    "raw_label": token.raw_label,
                    "normalized_label": token.normalized_label,
                    "arabic_value": token.arabic_value,
                    "char_type": token.char_type,
                    "confidence": round(token.confidence, 4),
                    "bbox": [token.x1, token.y1, token.x2, token.y2],
                }
            )

    letters_ar = "".join(token.arabic_value for token in letters_flat)
    digits_ar = "".join(token.arabic_value for token in digits_flat)
    raw_letters = "".join(token.normalized_label for token in letters_flat)
    raw_digits = "".join(token.normalized_label for token in digits_flat)
    display_summary_ar = " ".join(part for part in [letters_ar, digits_ar] if part).strip()
    all_display_tokens = letters_flat + digits_flat
    normalized_search_value = "".join(
        token.arabic_value for token in all_display_tokens if token.arabic_value.strip()
    )
    confidences = [token.confidence for token in filtered_tokens]
    plate_confidence = round(median(confidences), 4) if confidences else 0.0

    # ── Anti-hallucination gates ─────────────────────────────────────
    arabic_text_display = None

    if len(filtered_tokens) < MIN_TOKEN_COUNT or plate_confidence < MIN_PLATE_CONF_FOR_DISPLAY:
        display_summary_ar = "اللوحة غير واضحة"
        normalized_search_value = "LOW_CONFIDENCE"
        arabic_text_display = "اللوحة غير واضحة"
    elif any(t.arabic_value == "UNKNOWN_CLASS" for t in filtered_tokens):
        display_summary_ar = "نتيجة غير مؤكدة"
        normalized_search_value = "UNKNOWN_CLASS_DETECTED"
        arabic_text_display = "نتيجة غير مؤكدة"

    return PlateReadResult(
        raw_text_visual=" | ".join(raw_visual_rows),
        arabic_text_display=arabic_text_display if arabic_text_display else " | ".join(display_rows),
        display_summary_ar=display_summary_ar,
        normalized_search_value=normalized_search_value,
        letters_ar=letters_ar,
        digits_ar=digits_ar,
        raw_letters=raw_letters,
        raw_digits=raw_digits,
        plate_confidence=plate_confidence,
        token_count=len(filtered_tokens),
        row_count=len(rows),
        token_details=ordered_tokens,
    )


def serialize_plate_result(result: PlateReadResult) -> dict:
    return asdict(result)
