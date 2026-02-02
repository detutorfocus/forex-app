import { useState } from "react";
import { useLoadOnce } from "../hooks/useLoadOnce";
import { getTradeHistory } from "../../services/trading";

// If your structure differs, try one of these instead:
// import { useLoadOnce } from "./hooks/useLoadOnce";
// import { getTradeHistory } from "../services/trading";

type TradeHistoryRow = any;

export default function TradesPage() {
  const [rows, setRows] = useState<TradeHistoryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useLoadOnce(() => {
    const controller = new AbortController();
    let alive = true;

    (async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getTradeHistory({ signal: controller.signal });

        if (!alive) return;
        const list = Array.isArray(data) ? data : (data?.results ?? []);
        setRows(list);
      } catch (e: any) {
        if (!alive) return;
        if (e?.name === "AbortError") return;

        const status = e?.response?.status;
        if (status === 401) setError("Unauthorized (401). Please login again.");
        else if (status === 429) setError("Too many requests (429). Please wait a moment.");
        else setError(e?.message || "Failed to load trade history.");
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
      controller.abort();
    };
  });

  // ------- UI -------
  if (loading) return <div className="p-4">Loading trade history…</div>;

  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-600 font-medium mb-2">{error}</div>
        <div className="text-sm text-slate-600">
          If this is 401, your token is missing/expired. Re-login and retry.
        </div>
      </div>
    );
  }

  if (!rows.length) return <div className="p-4">No trade history found.</div>;

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-4">Trade History</h1>

      <div className="overflow-auto border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-2">Symbol</th>
              <th className="text-left p-2">Side</th>
              <th className="text-left p-2">Lots</th>
              <th className="text-left p-2">Open</th>
              <th className="text-left p-2">Close</th>
              <th className="text-left p-2">PnL</th>
              <th className="text-left p-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t: any, idx: number) => (
              <tr key={t?.id ?? idx} className="border-t">
                <td className="p-2">{t?.symbol ?? "-"}</td>
                <td className="p-2">{t?.side ?? t?.type ?? "-"}</td>
                <td className="p-2">{t?.lots ?? t?.volume ?? "-"}</td>
                <td className="p-2">{t?.open_price ?? t?.price_open ?? "-"}</td>
                <td className="p-2">{t?.close_price ?? t?.price_close ?? "-"}</td>
                <td className="p-2">{t?.pnl ?? t?.profit ?? "-"}</td>
                <td className="p-2">{t?.time ?? t?.closed_at ?? t?.created_at ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
