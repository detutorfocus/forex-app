import { api, clearAuth, setJwtTokens, setKeyToken } from "./api";

// src/services/auth.ts

// Storage keys (MUST match what LoginPage sets)
export const ACCESS_KEY = "accessToken";
export const REFRESH_KEY = "refreshToken";
export const KEY_TOKEN = "authKey"; // only if your backend returns it

// Getters
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function getKeyToken(): string | null {
  return localStorage.getItem(KEY_TOKEN);
}

// Setters (recommended)
export function setAuthTokens(params: { access: string; refresh: string; key?: string }) {
  localStorage.setItem(ACCESS_KEY, params.access);
  localStorage.setItem(REFRESH_KEY, params.refresh);

  if (params.key) {
    localStorage.setItem(KEY_TOKEN, params.key);
  } else {
    localStorage.removeItem(KEY_TOKEN);
  }
}

// Clear auth
export function clearAuth() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(KEY_TOKEN);
}

// Used by guards / router
export function isAuthenticated(): boolean {
  return Boolean(getAccessToken() || getKeyToken());
}

// Your AppLayout expects `logout` to exist.
// We clear tokens even if logout endpoint fails.
export async function logout() {
  try {
    const mod = await import("./api");
    const api = mod.default;

    // Try common logout endpoints (keep whichever your backend actually uses)
    await api.post("/api/logout/").catch(() =>
      api.post("/dj-rest-auth/logout/").catch(() => Promise.resolve())
    );
  } finally {
    clearAuth();
  }
}

/**
 * Compatibility object: some files do `import { auth } from "../services/auth"`
 */
export const auth = {
  getAccessToken,
  getRefreshToken,
  getKeyToken,
  setAuthTokens,
  clearAuth,
  isAuthenticated,
  logout,
};
