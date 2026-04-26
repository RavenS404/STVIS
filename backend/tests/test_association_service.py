from common.constants.enums import AssociationStatus
from common.utils.association import associate_entities


def test_association_pairs_each_plate_to_the_correct_vehicle():
    detections = [
        {"label": "vehicle", "confidence": 0.95, "bbox": [0, 0, 100, 120]},
        {"label": "vehicle", "confidence": 0.96, "bbox": [140, 0, 260, 120]},
        {"label": "car_plate", "confidence": 0.9, "bbox": [20, 80, 60, 100]},
        {"label": "car_plate", "confidence": 0.91, "bbox": [180, 82, 220, 100]},
        {"label": "using_mobile", "confidence": 0.94, "bbox": [15, 10, 45, 55]},
        {"label": "wrong_way", "confidence": 0.87, "bbox": [170, 12, 240, 70]},
    ]

    result = associate_entities(detections, min_plate_score=0.35, ambiguity_gap=0.12)

    assert len(result.vehicles) == 2
    assert result.vehicles[0].plate is not None
    assert result.vehicles[1].plate is not None
    assert result.vehicles[0].plate.bbox == (20.0, 80.0, 60.0, 100.0)
    assert result.vehicles[1].plate.bbox == (180.0, 82.0, 220.0, 100.0)
    assert result.vehicles[0].violations[0].label == "using_mobile"
    assert result.vehicles[1].violations[0].label == "wrong_way"


def test_association_marks_plate_as_ambiguous_when_scores_are_too_close():
    detections = [
        {"label": "vehicle", "confidence": 0.95, "bbox": [0, 0, 130, 120]},
        {"label": "vehicle", "confidence": 0.94, "bbox": [80, 0, 210, 120]},
        {"label": "car_plate", "confidence": 0.91, "bbox": [90, 75, 120, 96]},
    ]

    result = associate_entities(detections, min_plate_score=0.35, ambiguity_gap=0.2)

    assert len(result.vehicles) == 2
    assert any(vehicle.association_status == AssociationStatus.AMBIGUOUS for vehicle in result.vehicles)


def test_association_merges_windshield_anchor_into_the_detected_vehicle():
    detections = [
        {"label": "vehicle", "confidence": 0.97, "bbox": [0, 0, 300, 200]},
        {"label": "car windshield", "confidence": 0.94, "bbox": [50, 30, 250, 130]},
        {"label": "car_plate", "confidence": 0.91, "bbox": [90, 150, 170, 185]},
        {"label": "using_mobile", "confidence": 0.88, "bbox": [120, 55, 155, 115]},
    ]

    result = associate_entities(detections, min_plate_score=0.35, ambiguity_gap=0.08)

    assert len(result.vehicles) == 1
    assert result.vehicles[0].support_zone is not None
    assert result.vehicles[0].plate is not None
    assert result.vehicles[0].violations[0].label == "using_mobile"
