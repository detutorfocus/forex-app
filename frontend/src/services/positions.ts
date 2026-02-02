import { apiGet } from "../api/client";

export function fetchPositions() {
  return apiGet("/trading/live/positions/");
}

import { useEffect, useRef } from "react";

const didLoadRef = useRef(false);

useEffect(() => {
  if (didLoadRef.current) return;   // ✅ stops StrictMode double call
  didLoadRef.current = true;

  const controller = new AbortController();
  let mounted = true;

  async function load() {
    setPosBusy(true);
    setPosError(null);

    try {
      const res = await fetchLivePositions({ signal: controller.signal }); // pass signal
      if (!mounted) return;

      setPositions(Array.isArray(res) ? res : (res?.results ?? []));
    } catch (e: any) {
      if (!mounted) return;
      if (e?.name === "AbortError") return;

      const status = e?.response?.status;
      if (status === 401) setPosError("Unauthorized (401). Please login again.");
      else if (status === 429) setPosError("Too many requests (429). Please wait a moment.");
      else setPosError(e?.message || "Could not load positions.");
    } finally {
      if (mounted) setPosBusy(false);
    }
  }

  load();

  return () => {
    mounted = false;
    controller.abort();
  };
}, []);
