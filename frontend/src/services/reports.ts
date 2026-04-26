import { api } from "./api";
import type { ReportSummary } from "../app/types";

function normalizeReportSummary(data: ReportSummary): ReportSummary {
  return {
    ...data,
    total_cases: data.total_cases ?? 0,
    issued_cases: data.issued_cases ?? 0,
    rejected_cases: data.rejected_cases ?? 0,
    supervisor_cases: data.supervisor_cases ?? 0,
    average_plate_confidence: data.average_plate_confidence ?? null,
    violation_breakdown: data.violation_breakdown ?? {},
  };
}

export async function fetchReportSummary() {
  const { data } = await api.get<ReportSummary>("/reports/summary");
  return normalizeReportSummary(data);
}

export async function exportCasesCsv() {
  const { data } = await api.get<Blob>("/reports/export.csv", { responseType: "blob" });
  return data;
}
