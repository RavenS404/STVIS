import { api } from "./api";
import type { SystemHealth } from "../app/types";

function normalizeSystemHealth(data: SystemHealth): SystemHealth {
  return {
    ...data,
    components: data.components ?? {},
  };
}

export async function fetchSystemHealth() {
  const { data } = await api.get<SystemHealth>("/health/system");
  return normalizeSystemHealth(data);
}
