from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Iterable, Sequence

from common.constants.enums import AssociationStatus
from common.constants.violation_catalog import PLATE_BOX_LABEL, VIOLATION_CATALOG


@dataclass(slots=True)
class DetectionBox:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]

    @property
    def x1(self) -> float:
        return self.bbox[0]

    @property
    def y1(self) -> float:
        return self.bbox[1]

    @property
    def x2(self) -> float:
        return self.bbox[2]

    @property
    def y2(self) -> float:
        return self.bbox[3]

    @property
    def width(self) -> float:
        return max(self.x2 - self.x1, 1.0)

    @property
    def height(self) -> float:
        return max(self.y2 - self.y1, 1.0)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


@dataclass(slots=True)
class VehicleAssociation:
    vehicle: DetectionBox
    support_zone: DetectionBox | None = None
    plate: DetectionBox | None = None
    violations: list[DetectionBox] = field(default_factory=list)
    plate_score: float | None = None
    flags: list[str] = field(default_factory=list)
    association_status: AssociationStatus = AssociationStatus.CONFIDENT

    @property
    def violation_anchor(self) -> DetectionBox:
        return self.support_zone or self.vehicle


@dataclass(slots=True)
class AssociationOutcome:
    vehicles: list[VehicleAssociation]
    unmatched_plates: list[DetectionBox]
    unmatched_violations: list[DetectionBox]


def build_detection_boxes(detections: Iterable[dict]) -> list[DetectionBox]:
    items: list[DetectionBox] = []
    for item in detections:
        bbox = item["bbox"]
        items.append(
            DetectionBox(
                label=str(item["label"]),
                confidence=float(item["confidence"]),
                bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            )
        )
    return items


def _intersection(a: DetectionBox, b: DetectionBox) -> tuple[float, float, float, float] | None:
    x1 = max(a.x1, b.x1)
    y1 = max(a.y1, b.y1)
    x2 = min(a.x2, b.x2)
    y2 = min(a.y2, b.y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2, y2


def iou(a: DetectionBox, b: DetectionBox) -> float:
    overlap = _intersection(a, b)
    if overlap is None:
        return 0.0
    intersection_area = (overlap[2] - overlap[0]) * (overlap[3] - overlap[1])
    union_area = (a.width * a.height) + (b.width * b.height) - intersection_area
    return intersection_area / max(union_area, 1.0)


def contains_ratio(container: DetectionBox, inner: DetectionBox) -> float:
    overlap = _intersection(container, inner)
    if overlap is None:
        return 0.0
    intersection_area = (overlap[2] - overlap[0]) * (overlap[3] - overlap[1])
    return intersection_area / max(inner.width * inner.height, 1.0)


def normalized_distance(a: DetectionBox, b: DetectionBox) -> float:
    ax, ay = a.center
    bx, by = b.center
    diag = hypot(max(a.width, b.width), max(a.height, b.height))
    return min(hypot(ax - bx, ay - by) / max(diag, 1.0), 1.0)


def plate_vehicle_score(vehicle: DetectionBox, plate: DetectionBox) -> float:
    containment = contains_ratio(vehicle, plate)
    overlap = iou(vehicle, plate)
    distance = 1.0 - normalized_distance(vehicle, plate)
    return round((containment * 0.6) + (overlap * 0.2) + (distance * 0.2), 4)


def violation_vehicle_score(vehicle: DetectionBox, violation: DetectionBox) -> float:
    overlap = iou(vehicle, violation)
    distance = 1.0 - normalized_distance(vehicle, violation)
    return round((overlap * 0.65) + (distance * 0.35), 4)


def support_vehicle_score(vehicle: DetectionBox, support: DetectionBox) -> float:
    containment = contains_ratio(vehicle, support)
    overlap = iou(vehicle, support)
    distance = 1.0 - normalized_distance(vehicle, support)
    return round((containment * 0.55) + (overlap * 0.25) + (distance * 0.2), 4)


def _pick_best_candidate(
    scores: Sequence[tuple[int, float]],
    *,
    min_score: float,
    ambiguity_gap: float,
) -> tuple[int | None, float | None, bool]:
    ranked = sorted(scores, key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] < min_score:
        return None, None, False

    best_index, best_score = ranked[0]
    if len(ranked) == 1:
        return best_index, best_score, False

    ambiguous = (best_score - ranked[1][1]) < ambiguity_gap
    return best_index, best_score, ambiguous


def _build_vehicle_associations(items: Sequence[DetectionBox], *, ambiguity_gap: float) -> list[VehicleAssociation]:
    vehicles = [item for item in items if item.label == "vehicle"]
    windshields = [item for item in items if item.label == "car windshield"]

    if vehicles:
        associations = [VehicleAssociation(vehicle=vehicle) for vehicle in vehicles]
        for windshield in windshields:
            scores = [(index, support_vehicle_score(item.vehicle, windshield)) for index, item in enumerate(associations)]
            best_index, best_score, _ambiguous = _pick_best_candidate(
                scores,
                min_score=0.28,
                ambiguity_gap=max(ambiguity_gap * 0.6, 0.05),
            )
            if best_index is None:
                associations.append(VehicleAssociation(vehicle=windshield))
                continue

            association = associations[best_index]
            if association.support_zone is None:
                association.support_zone = windshield
                continue

            current_score = support_vehicle_score(association.vehicle, association.support_zone)
            if best_score is not None and best_score > current_score:
                association.support_zone = windshield
        return associations

    return [VehicleAssociation(vehicle=windshield) for windshield in windshields]


def associate_entities(
    detections: Iterable[dict],
    *,
    min_plate_score: float,
    ambiguity_gap: float,
) -> AssociationOutcome:
    items = build_detection_boxes(detections)
    associations = _build_vehicle_associations(items, ambiguity_gap=ambiguity_gap)
    plates = [item for item in items if item.label == PLATE_BOX_LABEL]
    violations = [item for item in items if item.label in VIOLATION_CATALOG]

    if not associations and (plates or violations):
        synthetic_bounds = [
            min(item.x1 for item in plates + violations),
            min(item.y1 for item in plates + violations),
            max(item.x2 for item in plates + violations),
            max(item.y2 for item in plates + violations),
        ]
        associations = [
            VehicleAssociation(
                vehicle=DetectionBox(
                    label="synthetic_vehicle",
                    confidence=max(item.confidence for item in plates + violations),
                    bbox=tuple(synthetic_bounds),
                )
            )
        ]

    unmatched_plates: list[DetectionBox] = []
    unmatched_violations: list[DetectionBox] = []
    claimed_vehicle_indexes: set[int] = set()

    for plate in plates:
        scores = [(index, plate_vehicle_score(item.vehicle, plate)) for index, item in enumerate(associations)]
        best_index, best_score, ambiguous = _pick_best_candidate(
            scores,
            min_score=min_plate_score,
            ambiguity_gap=ambiguity_gap,
        )
        if best_index is None:
            unmatched_plates.append(plate)
            continue

        association = associations[best_index]
        if association.plate is not None and best_index in claimed_vehicle_indexes:
            association.flags.append("multiple_plate_candidates")
            association.association_status = AssociationStatus.AMBIGUOUS
            unmatched_plates.append(plate)
            continue

        association.plate = plate
        association.plate_score = best_score
        claimed_vehicle_indexes.add(best_index)
        if ambiguous:
            association.flags.append("plate_association_ambiguous")
            association.association_status = AssociationStatus.AMBIGUOUS
        elif best_score is not None and best_score < max(min_plate_score + 0.1, 0.48):
            association.flags.append("plate_association_doubtful")
            association.association_status = AssociationStatus.DOUBTFUL

    for violation in violations:
        scores: list[tuple[int, float]] = []
        for index, association in enumerate(associations):
            zone_score = violation_vehicle_score(association.violation_anchor, violation)
            vehicle_score = violation_vehicle_score(association.vehicle, violation)
            scores.append((index, round(max(zone_score, vehicle_score * 0.88), 4)))

        best_index, _best_score, ambiguous = _pick_best_candidate(
            scores,
            min_score=0.24,
            ambiguity_gap=ambiguity_gap,
        )
        if best_index is None:
            unmatched_violations.append(violation)
            continue

        association = associations[best_index]
        association.violations.append(violation)
        if ambiguous:
            association.flags.append(f"violation_association_ambiguous:{violation.label}")
            association.association_status = AssociationStatus.AMBIGUOUS

    for association in associations:
        if association.plate is None:
            association.flags.append("plate_missing")
            association.association_status = (
                AssociationStatus.NO_PLATE
                if association.association_status == AssociationStatus.CONFIDENT
                else association.association_status
            )

    return AssociationOutcome(
        vehicles=associations,
        unmatched_plates=unmatched_plates,
        unmatched_violations=unmatched_violations,
    )
