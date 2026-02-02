import { useMemo, useState } from "react";
import { Card } from "../components/Card";
import { Button } from "../components/Button";

import { alexAnalyze, type AnalyzeResponse } from "../../services/assistant";
import { formatDecision } from "../../utils/formatDecision";
import { buildPlan, type TradeMode } from "../../utils/tradePlan";

const TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"];
const SYMBOLS = [
  "EURUSD",
  "GBPUSD",
  "USDJPY",
  "USDCHF",
  "USDCAD",
  "AUDUSD",
  "NZDUSD",
  "EURGBP",
  "EURJPY",
  "GBPJPY",
  "XAUUSD",
  "XAGUSD",
  "BTCUSD",
  "ETHUSD",
];

function pickDecisionObject(resp: AnalyzeResponse | null): any | null {
  if (!resp) return null;
  // Backend commonly returns { decision: {...}, status: 'OK', ... }
  return (resp as any).decision ?? (resp as any);
}

export default function AssistantPage() {
  const [symbol, setSymbol] = useState<string>("XAUUSD");
  const [timeframe, setTimeframe] = useState<string>("M15");
  const [notes, setNotes] = useState<string>("");
  const [mode, setMode] = useState<TradeMode>("CONSERVATIVE");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resp, setResp] = useState<AnalyzeResponse | null>(null);

  const decision = useMemo(() => pickDecisionObject(resp), [resp]);


  const plan = useMemo(() => {
    if (!decision) return null;
    try {
      return buildPlan(decision, mode);
    } catch {
      return null;
    }
  }, [decision, mode]);

  const onAnalyze = async () => {
    setBusy(true);
    setError(null);

    try {
      const data = await alexAnalyze({
        symbol,
        timeframe,
        bars: 300,
        notes,
      });
      setResp(data);
    } catch (e: any) {
      setResp(null);
      setError(e?.message ?? "Analyze failed");
    } finally {
      setBusy(false);
    }
  };

  const zones = useMemo(() =>{
      const d: any = decision;
      return d?.raw?.zones ?? [];
      }, [decision]);

  const marketClosed = zones.length === 0;

  const decisionText = useMemo(() => {
    if (!decision) return "";
    try {
      return formatDecision(decision);
    } catch {
      // Fallback if formatDecision signature differs
      return JSON.stringify(decision, null, 2);
    }
  }, [decision]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT: inputs */}
        <Card className="lg:col-span-1 p-4">
          <h2 className="text-xl font-semibold mb-4">Assistant</h2>

          <label className="block text-sm opacity-80 mb-1">Symbol</label>
          <select
            className="w-full rounded-md bg-transparent border border-white/10 p-2 mb-3"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
          >
            {SYMBOLS.map((s) => (
              <option key={s} value={s} className="bg-slate-900">
                {s}
              </option>
            ))}
          </select>

          <label className="block text-sm opacity-80 mb-1">Timeframe</label>
          <select
            className="w-full rounded-md bg-transparent border border-white/10 p-2 mb-3"
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
          >
            {TIMEFRAMES.map((tf) => (
              <option key={tf} value={tf} className="bg-slate-900">
                {tf}
              </option>
            ))}
          </select>

          <label className="block text-sm opacity-80 mb-1">Mode</label>
          <select
            className="w-full rounded-md bg-transparent border border-white/10 p-2 mb-3"
            value={mode}
            onChange={(e) => setMode(e.target.value as TradeMode)}
          >
            <option value="CONSERVATIVE" className="bg-slate-900">
              Conservative
            </option>
            <option value="BALANCED" className="bg-slate-900">
              Balanced
            </option>
            <option value="AGGRESSIVE" className="bg-slate-900">
              Aggressive
            </option>
          </select>

          <label className="block text-sm opacity-80 mb-1">Notes (optional)</label>
          <textarea
            className="w-full min-h-[110px] rounded-md bg-transparent border border-white/10 p-2 mb-4"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Anything Alex should consider…"
          />

          <Button disabled={busy} onClick={onAnalyze}>
            {busy ? "Analyzing…" : "Analyze"}
          </Button>

          {error ? <p className="text-red-400 text-sm mt-3">{error}</p> : null}
        </Card>

        {/* RIGHT: output */}
        <Card className="lg:col-span-2 p-4">
          <h3 className="text-lg font-semibold mb-3">Alex</h3>

          {!resp ? (
            <p className="opacity-70 text-sm">Run an analysis to see the decision and plan.</p>
          ) : (
            <div className="space-y-4">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed bg-white/5 border border-white/10 rounded-lg p-4">
                {decisionText}
              </pre>

              {/* Summary plan (kept simple for now) */}
              <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                <div className="text-sm font-semibold mb-2">Plan (summary)</div>

                {marketClosed ? (
                  <div className="mt-2 rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-3">
                    <div className="font-semibold text-yellow-300">Weekend / Market closed</div>
                    <div className="mt-1 text-sm text-yellow-200/90">
                      No fresh candles/zones. Try again when market opens or use last saved analysis.
                    </div>
                  </div>
                ) : plan?.summary ? (
                  <pre className="whitespace-pre-wrap text-sm">{plan.summary}</pre>
                ) : (
                  <p className="opacity-70 text-sm">
                    Plan unavailable (zones not suitable or decision has insufficient data).
                  </p>
                )}

              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
