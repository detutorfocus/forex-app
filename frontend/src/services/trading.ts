import { apiGet, apiPost } from "../api/client";

const API_BASE =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  (import.meta as any).env?.VITE_API_URL ||
  "http://127.0.0.1:8000";

function getAccessToken(): string {
  return (
    localStorage.getItem("fx_access_token") ||
    localStorage.getItem("access") ||
    localStorage.getItem("token") ||
    localStorage.getItem("authToken") ||
    ""
  );
}

export type Position = {
  id?: string | number;
  symbol?: string;
  side?: string;
  volume?: number;
  profit?: number;
};

export type LivePosition = any;
export type LiveOrder = any;
export type TradeHistoryRow = any;

export async function getLivePositions(opts?: { signal?: AbortSignal }) {
  return apiGet("/trading/live/positions/", { signal: opts?.signal });
}

export async function getLiveOrders(opts?: { signal?: AbortSignal }) {
  return apiGet("/trading/live/orders/", { signal: opts?.signal });
}

export async function getTradeHistory(opts?: { signal?: AbortSignal }) {
  return apiGet("/trading/live/history/", { signal: opts?.signal });
}

// Backwards-compatible names (in case older pages still import these)
export const fetchLivePositions = getLivePositions;
export const fetchTradeHistory = getTradeHistory;

export async function openTrade(payload: any, opts?: { signal?: AbortSignal }) {
  return apiPost("/trading/execute/", payload, { signal: opts?.signal });
}

export async function closeTrade(payload: any, opts?: { signal?: AbortSignal }) {
  return apiPost("/trading/close/", payload, { signal: opts?.signal });
}

/**
 * Audit export:
 * - auditExport("csv") returns a Blob you can download
 * - auditExport("json") returns parsed JSON
 */
export async function auditExport(
  format: "csv" | "json" = "json",
  opts?: { signal?: AbortSignal }
): Promise<Blob | any> {
  const token = getAccessToken();

  // If your backend uses a different base path, change ONLY this:
  const url = new URL("/audit/export", API_BASE);
  url.searchParams.set("format", format);

  const res = await fetch(url.toString(), {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(format === "json" ? { Accept: "application/json" } : {}),
    },
    signal: opts?.signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Audit export failed (${res.status})`);
  }

  return format === "csv" ? await res.blob() : await res.json();
}

/**
 * Audit verify:
 * Returns backend verification status JSON.
 */
export async function auditVerify(opts?: { signal?: AbortSignal }) {
  const token = getAccessToken();

  const url = new URL("/audit/verify/", API_BASE);

  const res = await fetch(url.toString(), {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    signal: opts?.signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Audit verify failed (${res.status})`);
  }

  return res.json();
}
