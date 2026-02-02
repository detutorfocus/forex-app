import api from "./api";
import { apiFetch } from "./api";

export type LivePosition = {
  ticket: number;
  symbol: string;
  type: string;
  volume: number;
  price_open: number;
  sl?: number | null;
  tp?: number | null;
  profit?: number | null;
};

export type LiveOrder = {
  ticket: number;
  symbol: string;
  type: string;
  volume: number;
  price_open: number;
  sl?: number | null;
  tp?: number | null;
};

export async function fetchLivePositions(): Promise<LivePosition[]> {
  // You likely have something like /api/trading/live/positions/
  // Update to match your trading/urls.py when you finalize it.
  const res = await api.get("/trading/live/positions/");
  return res.data ?? [];
}

export async function fetchLiveOrders(): Promise<LiveOrder[]> {
  const res = await api.get("/trading/live/orders/");
  return res.data ?? [];
}

export async function fetchTradeHistory(): Promise<any[]> {
  const res = await api.get("/trading/live/history/");
  return res.data?.results ?? res.data ?? [];
}

export async function closeTrade(ticket: number) {
  // example; update to match your close endpoint
  return api.post("/trading/live/close/", { ticket });
}

export async function emergencyCloseAll() {
  return api.post("/trading/live/emergency-close-all/", {});
}

export async function auditExport(format: "json" | "csv" = "json") {
  const res = await api.get(`/trading/audit/export?format=${format}`, {
    responseType: format === "csv" ? "blob" : "json",
  });
  return res.data;
}

export async function auditVerify() {
  const res = await api.get("/trading/audit/verify");
  return res.data;
}

