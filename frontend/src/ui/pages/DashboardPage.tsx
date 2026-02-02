import { useEffect, useMemo, useState } from "react";
import MarketChart from "../components/MarketChart";
import { fetchLivePositions } from "../../services/tradingHistory";
import { apiGet } from "../../api/client";

const positions = await apiGet("/trading/live/positions/");

type TimeframeOption = { label: string; value: string };

const TIMEFRAMES: TimeframeOption[] = [
  { label: "1m", value: "1m" },
  { label: "5m", value: "5m" },
  { label: "15m", value: "15m" },
  { label: "1h", value: "1h" },
  { label: "4h", value: "4h" },
  { label: "1d", value: "1d" },
];

export default function DashboardPage() {
  const [symbol, setSymbol] = useState("EURUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [positions, setPositions] = useState<any[]>([]);
  const [posError, setPosError] = useState<string | null>(null);
  const [posBusy, setPosBusy] = useState(false);

  const title = useMemo(() => `${symbol} • ${timeframe}`, [symbol, timeframe]);

 /* useEffect(() => {
    // Positions will 401 if you don't attach Authorization header in fetchLivePositions().
    // We show a friendly error so dashboard doesn't go blank.
    let mounted = true;

    async function load() {
      setPosBusy(true);
      setPosError(null);
      try {
        const res = await fetchLivePositions();
        if (!mounted) return;
        setPositions(Array.isArray(res) ? res : (res?.results ?? []));
      } catch (e: any) {
        if (!mounted) return;
        const status = e?.response?.status;
        if (status === 401) setPosError("Unauthorized (401). You are logged in, but your API call is missing the JWT Authorization header.");
        else setPosError("Could not load positions.");
      } finally {
        if (mounted) setPosBusy(false);
      }
    }

    load();
    const id = window.setInterval(load, 5000);
    return () => {
      mounted = false;
      window.clearInterval(id);
    };
  }, []);*/

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row md:items-end gap-3">
        <div className="flex-1">
          <div className="text-white/70 text-sm">Symbol</div>
          <input
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            className="w-full mt-1 rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-white outline-none"
            placeholder="EURUSD"
          />
        </div>

        <div className="w-full md:w-48">
          <div className="text-white/70 text-sm">Timeframe</div>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="w-full mt-1 rounded-xl bg-white/5 border border-white/10 px-3 py-2 text-white outline-none"
          >
            {TIMEFRAMES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div className="text-white/60 text-sm md:pb-2">{title}</div>
      </div>

      {/* Live chart */}
      <MarketChart symbol={symbol} timeframe={timeframe} />

      {/* Positions */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="text-lg font-semibold mb-3">Live Positions</div>

        {posError ? (
          <div className="text-red-300 text-sm">{posError}</div>
        ) : posBusy ? (
          <div className="text-white/60 text-sm">Loading…</div>
        ) : positions.length === 0 ? (
          <div className="text-white/60 text-sm">No open positions.</div>
        ) : (
          <div className="space-y-2">
            {positions.map((p, idx) => (
              <div key={idx} className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm">
                <div className="flex justify-between">
                  <div className="font-semibold">{p.symbol ?? p.instrument ?? "—"}</div>
                  <div className="text-white/60">{p.side ?? p.type ?? ""}</div>
                </div>
                <div className="mt-1 text-white/70">
                  {p.volume ? `Vol: ${p.volume} ` : ""}
                  {p.price_open ? `Open: ${p.price_open} ` : ""}
                  {p.profit != null ? `PnL: ${p.profit}` : ""}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
