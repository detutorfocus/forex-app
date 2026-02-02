import axios from "axios";
// src/api/client.ts
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from "../auth/tokenStore";


export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  headers: { "Content-Type": "application/json" },
});

// Optional: attach JWT automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});


//API client with auto-auth + auto-refresh on 401

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  (import.meta as any).env?.VITE_API_URL ||
  "http://127.0.0.1:8000";

// Change these if your backend uses different endpoints
const REFRESH_ENDPOINT = "/api/token/refresh/"; // SimpleJWT default
// If you use dj-rest-auth instead, it may be: "/dj-rest-auth/token/refresh/"

type ApiOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: any;
  headers?: Record<string, string>;
  auth?: boolean; // default true
  signal?: AbortSignal;
};

async function parseError(res: Response): Promise<string> {
  const ct = res.headers.get("content-type") || "";
  try {
    if (ct.includes("application/json")) {
      const data = await res.json();
      if (typeof data?.detail === "string") return data.detail;
      return JSON.stringify(data);
    }
    return (await res.text()) || `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const res = await fetch(`${API_BASE}${REFRESH_ENDPOINT}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) return null;

  const data = await res.json();
  // SimpleJWT returns { access: "..." } (sometimes also refresh)
  if (data?.access) {
    setTokens({ access: data.access, refresh: data.refresh });
    return data.access as string;
  }
  return null;
}

export async function request<T = any>(path: string, opts: ApiOptions = {}): Promise<T> {
  const {
    method = "GET",
    body,
    headers = {},
    auth = true,
    signal,
  } = opts;

  const url = path.startsWith("http") ? path : `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;

  const makeHeaders = (token?: string) => ({
    Accept: "application/json",
    ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
    ...headers,
    ...(auth && token ? { Authorization: `Bearer ${token}` } : {}),
  });

  let token = getAccessToken();

  // 1st attempt
  let res = await fetch(url, {
    method,
    headers: makeHeaders(token || undefined),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
    credentials: "omit",
  });

  // If unauthorized and we’re using auth, try refresh once
  if (res.status === 401 && auth) {
    const newToken = await refreshAccessToken();
    if (!newToken) {
      clearTokens();
      throw new Error("Session expired. Please log in again.");
    }

    token = newToken;
    res = await fetch(url, {
      method,
      headers: makeHeaders(token),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
      credentials: "include",
    });
  }

  if (!res.ok) {
    throw new Error(await parseError(res));
  }

  // some endpoints return 204
  if (res.status === 204) return null as any;

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;

  // fallback
  return (await res.text()) as any;
}

// Convenience helpers
export const apiGet = <T = any>(path: string, opts?: Omit<ApiOptions, "method">) =>
  request<T>(path, { ...opts, method: "GET" });

export const apiPost = <T = any>(path: string, body?: any, opts?: Omit<ApiOptions, "method" | "body">) =>
  request<T>(path, { ...opts, method: "POST", body });

export const apiDelete = <T = any>(path: string, opts?: Omit<ApiOptions, "method">) =>
  request<T>(path, { ...opts, method: "DELETE" });
