export type AlexAction = "BUY" | "SELL" | "WAIT";

export type Decision = {
  status?: string;
  action?: AlexAction;           // from backend
  confidence?: number;
  symbol?: string;
  timeframe?: string;
  price?: number;

  // optional fields you may already have
  reason?: string;
  raw?: any;
};

export type TradeMode = "CONSERVATIVE" | "ASSISTED" | "AGGRESSIVE";

export type PlanSide = {
  side: "BUY" | "SELL";
  entry: number;
  sl: number;
  tp1: number;
  tp2: number;
  tp3: number;
  rr1: number;
  rr2: number;
  rr3: number;
};

export type PlanResult = {
  mode: TradeMode;
  recommended: AlexAction;
  why: string[];
  buy?: PlanSide;
  sell?: PlanSide;
};

/** Round nicely for FX */
const r = (n: number) => Number(n.toFixed(5));

/**
 * Compute 3 take profits based on R-multiples.
 * TP1 = 1R, TP2 = 2R, TP3 = 3R by default.
 */
function computeTPs(entry: number, sl: number, side: "BUY" | "SELL") {
  const risk = Math.abs(entry - sl);
  const tp = (mult: number) => {
    if (side === "BUY") return entry + risk * mult;
    return entry - risk * mult;
  };
  return {
    tp1: tp(1),
    tp2: tp(2),
    tp3: tp(3),
  };
}

function rr(entry: number, sl: number, tp: number) {
  const risk = Math.abs(entry - sl);
  const reward = Math.abs(tp - entry);
  return risk === 0 ? 0 : reward / risk;
}

/**
 * Uses backend "plan ideas" if present, otherwise tries to infer a simple plan
 * from raw.zones if you still have that structure.
 *
 * If you already generate entry/sl/tp in backend, we can just read them instead.
 */
function inferIdeasFromDecision(d: Decision): { buy?: { entry: number; sl: number }; sell?: { entry: number; sl: number } } {
  // If your backend already returns these in some place, map them here.
  // Example if you already have d.raw.plan.buy.entry etc:
  const plan = d.raw?.plan;
  if (plan?.buy?.entry && plan?.buy?.sl) {
    return { buy: { entry: Number(plan.buy.entry), sl: Number(plan.buy.sl) }, sell: plan?.sell?.entry && plan?.sell?.sl ? { entry: Number(plan.sell.entry), sl: Number(plan.sell.sl) } : undefined };
  }

  // If you still have zones list, we can derive a simple fallback:
  const zones: any[] = d.raw?.zones ?? [];
  if (!zones.length || typeof d.price !== "number") return {};

  // Pick nearest demand as BUY idea, nearest supply as SELL idea
  const price = d.price;

  const demands = zones.filter(z => (z.type || "").toUpperCase() === "DEMAND");
  const supplies = zones.filter(z => (z.type || "").toUpperCase() === "SUPPLY");

  const dist = (z: any) => Math.min(Math.abs(price - z.low), Math.abs(price - z.high), Math.abs(price - (z.level ?? price)));

  const nearestDemand = demands.sort((a, b) => dist(a) - dist(b))[0];
  const nearestSupply = supplies.sort((a, b) => dist(a) - dist(b))[0];

  const buy = nearestDemand
    ? {
        entry: Number(nearestDemand.high ?? nearestDemand.level ?? price),
        sl: Number(nearestDemand.low ?? (Number(nearestDemand.high ?? price) - 0.001)),
      }
    : undefined;

  const sell = nearestSupply
    ? {
        entry: Number(nearestSupply.low ?? nearestSupply.level ?? price),
        sl: Number(nearestSupply.high ?? (Number(nearestSupply.low ?? price) + 0.001)),
      }
    : undefined;

  return { buy, sell };
}

/**
 * Mode logic:
 * - CONSERVATIVE: obey backend action strictly (WAIT until confirmed)
 * - ASSISTED: if plan exists and confidence >= minConf => recommend BUY/SELL but require click
 * - AGGRESSIVE: if plan exists => recommend BUY/SELL immediately (still shows warning)
 */
export function buildPlan(d: Decision, mode: TradeMode, minConf = 70): PlanResult {
  const why: string[] = [];

  const conf = Number(d.confidence ?? 0);
  const backendAction: AlexAction = (d.action ?? "WAIT") as AlexAction;

  const ideas = inferIdeasFromDecision(d);

  const buyIdea = ideas.buy;
  const sellIdea = ideas.sell;

  const buy = buyIdea
    ? (() => {
        const tps = computeTPs(buyIdea.entry, buyIdea.sl, "BUY");
        return {
          side: "BUY" as const,
          entry: r(buyIdea.entry),
          sl: r(buyIdea.sl),
          tp1: r(tps.tp1),
          tp2: r(tps.tp2),
          tp3: r(tps.tp3),
          rr1: Number(rr(buyIdea.entry, buyIdea.sl, tps.tp1).toFixed(2)),
          rr2: Number(rr(buyIdea.entry, buyIdea.sl, tps.tp2).toFixed(2)),
          rr3: Number(rr(buyIdea.entry, buyIdea.sl, tps.tp3).toFixed(2)),
        };
      })()
    : undefined;

  const sell = sellIdea
    ? (() => {
        const tps = computeTPs(sellIdea.entry, sellIdea.sl, "SELL");
        return {
          side: "SELL" as const,
          entry: r(sellIdea.entry),
          sl: r(sellIdea.sl),
          tp1: r(tps.tp1),
          tp2: r(tps.tp2),
          tp3: r(tps.tp3),
          rr1: Number(rr(sellIdea.entry, sellIdea.sl, tps.tp1).toFixed(2)),
          rr2: Number(rr(sellIdea.entry, sellIdea.sl, tps.tp2).toFixed(2)),
          rr3: Number(rr(sellIdea.entry, sellIdea.sl, tps.tp3).toFixed(2)),
        };
      })()
    : undefined;

  if (backendAction === "WAIT") {
    why.push("No confirmed entry trigger yet (backend returned WAIT).");
  }
  if (conf < minConf) {
    why.push(`Confidence ${conf}% is below threshold (${minConf}%).`);
  }
  if (!buy && !sell) {
    why.push("No valid plan ideas available to compute entry/SL/TP.");
  }

  // Decide recommendation based on mode
  let recommended: AlexAction = "WAIT";

  if (mode === "CONSERVATIVE") {
    recommended = backendAction;
    if (recommended === "WAIT") why.push("Conservative mode: will not suggest entry without confirmation.");
  }

  if (mode === "ASSISTED") {
    if ((buy || sell) && conf >= minConf) {
      // If backend already said BUY/SELL, follow it; else pick nearer idea
      if (backendAction === "BUY" || backendAction === "SELL") {
        recommended = backendAction;
      } else {
        // choose whichever exists; if both exist, default to BUY idea first (you can change this rule)
        recommended = buy ? "BUY" : (sell ? "SELL" : "WAIT");
      }
      why.push("Assisted mode: shows a recommendation, but requires manual confirm to execute.");
    } else {
      recommended = "WAIT";
      why.push("Assisted mode: waiting due to missing plan or low confidence.");
    }
  }

  if (mode === "AGGRESSIVE") {
    if (buy || sell) {
      if (backendAction === "BUY" || backendAction === "SELL") recommended = backendAction;
      else recommended = buy ? "BUY" : (sell ? "SELL" : "WAIT");
      why.push("Aggressive mode: will recommend entry as soon as a plan exists.");
      why.push("Warning: higher risk of false entries in chop/range.");
    } else {
      recommended = "WAIT";
      why.push("Aggressive mode: still waiting because no plan is available.");
    }
  }

  return { mode, recommended, why, buy, sell };
}
