import { useEffect, useRef } from "react";

export function useLoadOnce(effect: () => void | (() => void)) {
  const didRun = useRef(false);

  useEffect(() => {
    if (didRun.current) return; // prevents StrictMode double-run in dev
    didRun.current = true;
    return effect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
