import { api } from "./api";
import type { CaseDetail, CaseListItem, PaginatedResponse } from "../app/types";

function normalizeCaseListItem(item: CaseListItem): CaseListItem {
  return {
    ...item,
    review_flags: Array.isArray(item.review_flags) ? item.review_flags : [],
    violations: Array.isArray(item.violations) ? item.violations : [],
  };
}

function normalizeCaseDetail(detail: CaseDetail): CaseDetail {
  return {
    ...detail,
    ...normalizeCaseListItem(detail),
    manual_override_payload: detail.manual_override_payload ?? {},
    plate_read: detail.plate_read ?? null,
    assets: Array.isArray(detail.assets) ? detail.assets : [],
    model_versions: detail.model_versions ?? {},
    debug_payload: detail.debug_payload ?? {},
  };
}

export async function fetchCases(params: Record<string, unknown>) {
  const { data } = await api.get<PaginatedResponse<CaseListItem>>("/cases", { params });
  return {
    ...data,
    items: Array.isArray(data.items) ? data.items.map(normalizeCaseListItem) : [],
  };
}

export async function fetchCaseDetail(caseId: string) {
  const { data } = await api.get<CaseDetail>(`/cases/${caseId}`);
  return normalizeCaseDetail(data);
}

export async function applyCaseDecision(caseId: string, payload: Record<string, unknown>) {
  const { data } = await api.post<{ message: string }>(`/cases/${caseId}/decision`, payload);
  return data;
}

export async function rerunEvent(eventId: string) {
  const { data } = await api.post<{ message: string }>(`/cases/events/${eventId}/rerun`);
  return data;
}

export async function fetchEvidenceBlob(url: string) {
  const { data } = await api.get<Blob>(url.replace("/api/v1", ""), { responseType: "blob" });
  return data;
}
