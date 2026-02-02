// src/services/api.ts
import axios from "axios";
import { getAccessToken, getKeyToken, clearAuth } from "./auth";
import { apiGet } from "./api/client";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000",
});

export const apiClient = axios.create({ baseURL: "http://127.0.0.1:8000"});

// Attach auth header to every request
apiClient.interceptors.request.use((config) => {
  const access = getAccessToken();
  const key = getKeyToken();

  config.headers = config.headers ?? {};

  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  } else if (key) {
    config.headers.Authorization = `Token ${key}`;
  }

  return config;
});

// Auto-clear tokens on 401 (optional, but helps stop “stuck” sessions)
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      clearAuth();
    }
    return Promise.reject(err);
  }
);

// Some files want: import api from "...";
export default api;

// Optional helper (only keep if you use it somewhere)
export async function apiFetch<T = any>(config: Parameters<typeof api.request>[0]) {
  const res = await api.request<T>(config);
  return res.data;
}
