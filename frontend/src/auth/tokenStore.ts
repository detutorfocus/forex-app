// src/auth/tokenStore.ts

// Your storage currently contains multiple token keys.
// We'll READ in a safe priority order and WRITE to a single consistent set.

const ACCESS_KEYS = ["fx_access_token", "access", "accessToken", "authToken"];
const REFRESH_KEYS = ["fx_refresh_token", "refresh", "refreshToken", "fx_refresh_token"];

export function getAccessToken(): string | null {
  for (const k of ACCESS_KEYS) {
    const v = localStorage.getItem(k);
    if (v) return v;
  }
  return null;
}

export function getRefreshToken(): string | null {
  for (const k of REFRESH_KEYS) {
    const v = localStorage.getItem(k);
    if (v) return v;
  }
  return null;
}

// We STANDARDIZE writes so everything is consistent going forward
export function setTokens(tokens: { access?: string; refresh?: string }) {
  if (tokens.access) {
    localStorage.setItem("fx_access_token", tokens.access);
    localStorage.setItem("access", tokens.access); // keep compatibility
  }
  if (tokens.refresh) {
    localStorage.setItem("fx_refresh_token", tokens.refresh);
    localStorage.setItem("refresh", tokens.refresh); // keep compatibility
  }
}

export function clearTokens() {
  const allKeys = new Set([...ACCESS_KEYS, ...REFRESH_KEYS, "user"]);
  for (const k of allKeys) localStorage.removeItem(k);
}

export function isLoggedIn() {
  return !!getAccessToken();
}
