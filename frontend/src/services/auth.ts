import { api } from "./api";
import type { CurrentUser } from "../app/types";

export async function loginRequest(username: string, password: string) {
  const { data } = await api.post<{ access_token: string; token_type: string }>("/auth/login", {
    username,
    password,
  });
  return data;
}

export async function fetchCurrentUser() {
  const { data } = await api.get<CurrentUser>("/auth/me");
  return data;
}
