import { useEffect, useState } from "react";

export interface Loaded<T> { data: T | undefined; error: Error | undefined; loading: boolean; retry: () => void }

// Keeps the previous data while the next request loads, so the replay does not flash.
export function useApi<T>(fn: (() => Promise<T>) | null, deps: unknown[]): Loaded<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<Error>();
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!fn) return;
    let live = true;
    setLoading(true);
    fn().then(
      (d) => { if (live) { setData(d); setError(undefined); setLoading(false); } },
      (e: Error) => { if (live) { setError(e); setLoading(false); } },
    );
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, error, loading, retry: () => setTick((t) => t + 1) };
}
