from pydantic import BaseModel


class DashboardSummary(BaseModel):
    cases_by_state: dict[str, int]
    violations_by_code: dict[str, int]
    queue_depth: int
    escalations: int
    issued_today: int
    recent_cases: list[dict]
