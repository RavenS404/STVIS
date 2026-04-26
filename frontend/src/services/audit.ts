import { api } from "./api";
import type { AuditLog, PaginatedResponse } from "../app/types";

export async function fetchAuditLogs(page = 1, params?: Record<string, unknown>) {
  const { data } = await api.get<PaginatedResponse<AuditLog>>("/audit", { params: { page, ...params } });
  return data;
}
