import { api } from "./api";
import type { DashboardSummary } from "../app/types";

function normalizeDashboardSummary(data: DashboardSummary): DashboardSummary {
  return {
    ...data,
    cases_by_state: data.cases_by_state ?? {},
    violations_by_code: data.violations_by_code ?? {},
    queue_depth: data.queue_depth ?? 0,
    escalations: data.escalations ?? 0,
    issued_today: data.issued_today ?? 0,
    recent_cases: Array.isArray(data.recent_cases) ? data.recent_cases : [],
  };
}

export async function fetchDashboardSummary() {
  const { data } = await api.get<DashboardSummary>("/dashboard/summary");
  return normalizeDashboardSummary(data);
}
