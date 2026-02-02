export type TradeRowData = {
  id: string;
  symbol: string;
  side: "BUY" | "SELL" | "—";
  lot: number | null;
  pnl: number | null;
};

export function TradeRow({
  t,
  onClick,
  selected,
}: {
  t: TradeRowData;
  onClick?: () => void;
  selected?: boolean;
}) {
  const sideClass =
    t.side === "BUY"
      ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/20"
      : t.side === "SELL"
      ? "bg-rose-500/15 text-rose-200 border-rose-500/20"
      : "bg-white/5 text-slate-200 border-white/10";

  const pnlClass =
    t.pnl == null
      ? "text-slate-200"
      : t.pnl >= 0
      ? "text-emerald-300"
      : "text-rose-300";

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "w-full text-left px-3 py-3 transition rounded-xl",
        "hover:bg-white/5",
        selected ? "bg-white/5 ring-1 ring-white/10" : "",
      ].join(" ")}
    >
      <div className="grid grid-cols-[1.2fr_.8fr_.7fr_.9fr] items-center gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold text-slate-100">
            {t.symbol}
          </div>
          <div className="text-xs text-slate-400">Symbol</div>
        </div>

        <div className="justify-self-start">
          <span className={`inline-flex items-center rounded-full border px-2 py-1 text-xs ${sideClass}`}>
            {t.side}
          </span>
          <div className="mt-1 text-xs text-slate-400">Side</div>
        </div>

        <div className="text-right">
          <div className="text-sm font-medium text-slate-100">
            {t.lot == null ? "—" : t.lot}
          </div>
          <div className="text-xs text-slate-400">Lot</div>
        </div>

        <div className="text-right">
          <div className={`text-sm font-semibold ${pnlClass}`}>
            {t.pnl == null ? "—" : t.pnl.toFixed(2)}
          </div>
          <div className="text-xs text-slate-400">P/L</div>
        </div>
      </div>
    </button>
  );
}
