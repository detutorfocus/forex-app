import { useEffect, useState } from "react";
import { apiGet } from "../api/client";
import { fetchPositions } from "../services/positions";


export default function PositionsPage() {
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  import { useState } from "react";
import { useLoadOnce } from "../hooks/useLoadOnce";
import { getLivePositions } from "../../services/trading";

 useLoadOnce(() => {
    const controller = new AbortController();
    let alive = true;

    (async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getLivePositions({ signal: controller.signal });
        if (!alive) return;

        const rows = Array.isArray(data) ? data : (data?.results ?? []);
        setPositions(rows);
      } catch (e: any) {
        if (!alive) return;
        if (e?.name === "AbortError") return;

        const status = e?.response?.status;
        if (status === 401) setError("Unauthorized (401). Please login again.");
        else if (status === 429) setError("Too many requests (429). Please wait a moment.");
        else setError(e?.message || "Failed to load positions.");
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
      controller.abort();
    };
  });

  // render...
}
  if (loading) return <p>Loading positions…</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;

if (!positions.length) return <div>No open positions.</div>;


  return (
    <div>
      <h2>Open Positions</h2>
      <pre>{JSON.stringify(positions, null, 2)}</pre>
    </div>
  );
}
