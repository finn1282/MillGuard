import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, clearCache, USE_FIXTURES } from "./api";
import { addHours } from "./format";
import type { LiveStatus, Marker, Meta } from "./types";
import { useApi } from "./useApi";

interface Ctx {
  at: string | undefined;
  setAt: (t: string) => void;
  playing: boolean; setPlaying: (p: boolean) => void;
  step: (h: number) => void;
  meta: Meta | undefined;
  markers: Marker[];
  bookmarks: Marker[];
  nextBookmark: () => void;
  live: LiveStatus | null; // v1.14: an active live session; the clock then follows live_at
}

const ClockCtx = createContext<Ctx>(null!);

export function ClockProvider({ children }: { children: ReactNode }) {
  const meta = useApi(api.meta, []);
  const marks = useApi(api.markers, []);
  // ?at= in the URL sets the starting time (presenter deep links).
  const [at, setAtRaw] = useState<string | undefined>(() => new URLSearchParams(location.search).get("at") ?? undefined);
  const [playing, setPlaying] = useState(false);
  const live = useLive();

  const markers = marks.data ?? [];
  const bookmarks = useMemo(
    () => markers.filter((m) => m.kind === "bookmark").sort((a, b) => a.t.localeCompare(b.t)), [markers]);

  // Start on the first bookmark (quiet night in the demo), else the end of the replay.
  useEffect(() => {
    if (at) return;
    if (bookmarks.length) setAtRaw(bookmarks[0].t);
    else if (marks.error && meta.data) setAtRaw(meta.data.replay.end);
  }, [at, bookmarks, marks.error, meta.data]);

  const setAt = useCallback((t: string) => { if (!live) { setPlaying(false); setAtRaw(t); } }, [live]);
  useEffect(() => { if (live) setPlaying(false); }, [live]);

  const step = useCallback((h: number) => {
    if (live) return;
    setAtRaw((cur) => {
      if (!cur) return cur;
      const next = addHours(cur, h);
      const r = meta.data?.replay;
      if (r && (next < r.start || next > r.end)) return cur;
      return next;
    });
  }, [meta.data, live]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => step(meta.data?.replay.step_h ?? 1), 900);
    return () => clearInterval(id);
  }, [playing, step, meta.data]);

  const nextBookmark = useCallback(() => {
    if (!bookmarks.length || live) return;
    const i = bookmarks.findIndex((b) => b.t === at);
    setAt(bookmarks[(i + 1) % bookmarks.length].t);
  }, [bookmarks, at, setAt, live]);

  return (
    <ClockCtx.Provider value={{
      at: (live && live.live_at) || at, setAt, playing, setPlaying, step, meta: meta.data, markers, bookmarks, nextBookmark, live,
    }}>
      {children}
    </ClockCtx.Provider>
  );
}

export const useClock = () => useContext(ClockCtx);

// Polls GET /api/live every second (never in fixture mode). Three failures in a row end live mode;
// the replay clock underneath is never touched, so it returns unchanged.
function useLive(): LiveStatus | null {
  const [live, setLive] = useState<LiveStatus | null>(null);
  const session = useRef<string | null>(null);
  useEffect(() => {
    if (USE_FIXTURES) return;
    let stop = false, fails = 0;
    const tick = () => api.live().then(
      (l) => {
        if (stop) return;
        fails = 0;
        const on = l?.enabled ? l : null;
        if ((on?.session_id ?? null) !== session.current) { session.current = on?.session_id ?? null; clearCache(); }
        setLive(on);
      },
      () => { if (!stop && ++fails >= 3) setLive(null); },
    );
    tick();
    const id = setInterval(tick, 1000);
    return () => { stop = true; clearInterval(id); };
  }, []);
  return live;
}
