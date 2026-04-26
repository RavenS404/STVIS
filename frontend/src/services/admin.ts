import { api } from "./api";
import type { DeviceEntry, ModelProfile, SettingEntry, UserEntry } from "../app/types";

export async function fetchUsers() {
  const { data } = await api.get<UserEntry[]>("/admin/users");
  return data;
}

export async function createUser(payload: Record<string, unknown>) {
  const { data } = await api.post<UserEntry>("/admin/users", payload);
  return data;
}

export async function fetchDevices() {
  const { data } = await api.get<DeviceEntry[]>("/admin/devices");
  return data;
}

export async function createDevice(payload: Record<string, unknown>) {
  const { data } = await api.post<{ device: DeviceEntry; plain_token: string }>("/admin/devices", payload);
  return data;
}

export async function rotateDeviceToken(deviceId: string) {
  const { data } = await api.post<{ device: DeviceEntry; plain_token: string }>(`/admin/devices/${deviceId}/rotate-token`);
  return data;
}

export async function fetchSettings() {
  const { data } = await api.get<SettingEntry[]>("/admin/settings");
  return data;
}

export async function updateSetting(key: string, value_json: unknown) {
  const { data } = await api.put<SettingEntry>(`/admin/settings/${key}`, { value_json });
  return data;
}

export async function fetchModels() {
  const { data } = await api.get<ModelProfile[]>("/admin/models");
  return data;
}
