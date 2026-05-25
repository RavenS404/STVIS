from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"


class EventProcessingStatus(StrEnum):
    RECEIVED = "received"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InferenceRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AssetKind(StrEnum):
    ORIGINAL = "original"
    PREVIEW = "preview"
    ANNOTATED_EVENT = "annotated_event"
    VEHICLE_CROP = "vehicle_crop"
    PLATE_CROP = "plate_crop"
    ANNOTATED_CASE = "annotated_case"
    VIOLATIONS_ANNOTATED = "violations_annotated"
    DRIVER_ZOOM = "driver_zoom"


class AssociationStatus(StrEnum):
    CONFIDENT = "confident"
    DOUBTFUL = "doubtful"
    AMBIGUOUS = "ambiguous"
    NO_PLATE = "no_plate"


class CaseReviewState(StrEnum):
    DIRECT_ISSUE_READY = "direct_issue_ready"
    SUPERVISOR_REVIEW_REQUIRED = "supervisor_review_required"
    ISSUED = "issued"
    REJECTED = "rejected"
    NO_VIOLATION = "no_violation"


class DecisionSource(StrEnum):
    SYSTEM = "system"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class ModelKey(StrEnum):
    VIOLATION_DETECTION = "violation_detection"
    PLATE_DETECTION = "plate_detection"


class ViolationCode(StrEnum):
    UNFASTENED_SEAT_BELT = "unfastened_seat_belt"
    USING_MOBILE = "using_mobile"
    WRONG_WAY = "wrong_way"
