import React, { useEffect, useMemo, useRef, useState } from "react";
import * as LWC from "lightweight-charts";

type Props = {
  symbol: string;
  timeframe: string; // e.g. "1m" | "5m" | "15m" | "1h" | "4h" | "1d"
};

/**
 * Robust Live candlestick chart using lightweight-charts + WebSocket feed.
 *
 * Expected WS message shapes (any of these):
 *  - { time, open, high, low, close }
 *  - { type: "candle", data: { time, open, high, low, close } }
 *  - { candle: { time, open, high, low, close } }
 * where `time` may be: epoch seconds, epoch ms, ISO string, or {t:...}
 */
export default function MarketChart({ symbol, timeframe }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  const chartRef = useRef<LWC.IChartApi | null>(null);
  const seriesRef = useRef<any>(null); // supports both v4 and v5 series types
  const wsRef = useRef<WebSocket | null>(null);
  const lastTimeRef = useRef<number>(0);

  const [status, setStatus] = useState<"connecting" | "open" | "closed" | "error">("connecting");

  const wsUrl = useMemo(() => {
    const envBase = (import.meta as any).env?.VITE_WS_BASE as string | undefined;

    const loc = window.location;
    const proto = loc.protocol === "https:" ? "wss" : "ws";
    const host = loc.hostname;
    const port = loc.port === "5173" ? "8000" : loc.port;
    const base = envBase ?? `${proto}://${host}${port ? `:${port}` : ""}`;

    return `${base}/ws/market/${encodeURIComponent(symbol)}/${encodeURIComponent(timeframe)}/`;
  }, [symbol, timeframe]);

  function parseTime(raw: any): number | null {
    if (raw == null) return null;

    const t = raw.t ?? raw.time ?? raw.timestamp ?? raw;
    if (typeof t === "number" && Number.isFinite(t)) {
      return t > 10_000_000_000 ? Math.floor(t / 1000) : Math.floor(t);
    }
    if (typeof t === "string") {
      const n = Number(t);
      if (Number.isFinite(n)) {
        return n > 10_000_000_000 ? Math.floor(n / 1000) : Math.floor(n);
      }
      const d = new Date(t);
      const ms = d.getTime();
      if (!Number.isFinite(ms)) return null;
      return Math.floor(ms / 1000);
    }
    return null;
  }

  function normalizeCandle(payload: any): LWC.CandlestickData<LWC.UTCTimestamp> | null {
    const c = payload?.data ?? payload?.candle ?? payload ?? null;
    if (!c) return null;

    const timeSec = parseTime(c.time ?? c.t ?? c.timestamp);
    if (!timeSec || timeSec <= 0) return null;

    const open = Number(c.open);
    const high = Number(c.high);
    const low = Number(c.low);
    const close = Number(c.close);

    if (![open, high, low, close].every((v) => Number.isFinite(v))) return null;

    const hi = Math.max(high, open, close);
    const lo = Math.min(low, open, close);

    return {
      time: timeSec as LWC.UTCTimestamp,
      open,
      high: hi,
      low: lo,
      close,
    };
  }

  // Create chart once
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const width = Math.max(320, el.clientWidth || 0);
    const height = Math.max(240, el.clientHeight || 0);

    const chart = LWC.createChart(el, {
      width,
      height,
      layout: { background: { color: "#0b1020" }, textColor: "#d1d5db" },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.05)" },
        horzLines: { color: "rgba(255,255,255,0.05)" },
      },
      timeScale: { timeVisible: true, secondsVisible: false },
      rightPriceScale: { borderVisible: false },
      crosshair: { mode: 0 as any },
    });

    // ✅ v4 uses addCandlestickSeries()
    // ✅ v5 uses addSeries(CandlestickSeries, options)
    const seriesOptions = {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    };

    let series: any = null;

    const anyChart = chart as any;
    const anyLWC = LWC as any;

    if (typeof anyChart.addCandlestickSeries === "function") {
      series = anyChart.addCandlestickSeries(seriesOptions);
    } else if (typeof anyChart.addSeries === "function" && anyLWC.CandlestickSeries) {
      series = anyChart.addSeries(anyLWC.CandlestickSeries, seriesOptions);
    } else {
      // If you ever hit this, your lightweight-charts version is very unusual.
      throw new Error("Unsupported lightweight-charts API: cannot create candlestick series.");
    }

    chartRef.current = chart;
    seriesRef.current = series;
    lastTimeRef.current = 0;

    const ro = new ResizeObserver(() => {
      const w = Math.max(320, el.clientWidth || 0);
      const h = Math.max(240, el.clientHeight || 0);
      chart.applyOptions({ width: w, height: h });
      chart.timeScale().fitContent();
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      try {
        chart.remove();
      } catch {}
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // WebSocket per symbol/timeframe
  useEffect(() => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {}
      wsRef.current = null;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => setStatus("open");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("error");

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        const candle = normalizeCandle(msg);
        if (!candle) return;

        const t = Number(candle.time);
        if (lastTimeRef.current && t < lastTimeRef.current) return;
        lastTimeRef.current = Math.max(lastTimeRef.current, t);

        const series = seriesRef.current;
        if (!series) return;

        series.update(candle);
      } catch {
        // ignore malformed messages
      }
    };

    return () => {
      try {
        ws.close();
      } catch {}
    };
  }, [wsUrl]);

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-sm text-white/80">
          {symbol} • {timeframe}
        </div>
        <div className="text-xs text-white/60">WS: {status}</div>
      </div>

      <div ref={containerRef} className="h-[360px] w-full" />
    </div>
  );
}
