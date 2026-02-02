import { api } from "./api";

export async function alexAnalyze(payload: { symbol: string; timeframe?: string; notes?: string }) {
  // ai_assistant/urls.py -> /ai/alex/analyze/ (and /ai_assistant/alex/analyze/)
  const res = await api.post("/ai/alex/analyze/", payload);
  return res.data;
}
