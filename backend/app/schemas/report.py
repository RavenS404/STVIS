from pydantic import BaseModel


class ReportSummary(BaseModel):
    total_cases: int
    issued_cases: int
    rejected_cases: int
    supervisor_cases: int
    average_plate_confidence: float | None
    violation_breakdown: dict[str, int]
