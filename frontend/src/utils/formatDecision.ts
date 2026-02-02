export function formatDecision(decision: any) {
  if (!decision) return "No decision returned.";

  const d = decision.decision ?? decision;

  const lines: string[] = [];
  lines.push(`Action: ${d.action ?? "—"}  |  Confidence: ${d.confidence ?? "—"}%`);
  lines.push(`Symbol: ${d.symbol ?? "—"}  |  Timeframe: ${d.timeframe ?? "—"}`);
  if (d.price != null) lines.push(`Price: ${d.price}`);
  if (d.reason) lines.push(`Reason: ${String(d.reason).replaceAll("_", " ")}`);

  // Optional: show zones nicely
  const zones = d.raw?.zones;
  if (Array.isArray(zones) && zones.length) {
    lines.push("");
    lines.push("Zones:");
    for (const z of zones.slice(0, 5)) {
      lines.push(`• ${z.type}: ${z.low} → ${z.high} (strength ${z.strength ?? "—"})`);
    }
  }

  return lines.join("\n");
}
