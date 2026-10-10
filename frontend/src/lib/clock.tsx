import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "./api";
import { addHours } from "./format";
import type { Marker, Meta } from "./types";
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
}

const ClockCtx = createContext<Ctx>(null!);

export function ClockProvider({ children }: { children: ReactNode }) {
  const meta = useApi(api.meta, []);
  const marks = useApi(api.markers, []);
  const [at, setAtRaw] = useState<string>();
  const [playing, setPlaying] = useState(false);

  const markers = marks.data ?? [];
  const bookmarks = useMemo(
    () => markers.filter((m) => m.kind === "bookmark").sort((a, b) => a.t.localeCompare(b.t)), [markers]);

  // Start on the first bookmark (quiet night in the demo), else the end of the replay.
  useEffect(() => {
    if (at) return;
    if (bookmarks.length) setAtRaw(bookmarks[0].t);
    else if (marks.error && meta.data) setAtRaw(meta.data.replay.end);
  }, [at, bookmarks, marks.error, meta.data]);

  const setAt = useCallback((t: string) => { setPlaying(false); setAtRaw(t); }, []);

  const step = useCallback((h: number) => {
    setAtRaw((cur) => {
      if (!cur) return cur;
      const next = addHours(cur, h);
      const r = meta.data?.replay;
      if (r && (next < r.start || next > r.end)) return cur;
      return next;
    });
  }, [meta.data]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => step(meta.data?.replay.step_h ?? 1), 900);
    return () => clearInterval(id);
  }, [playing, step, meta.data]);

  const nextBookmark = useCallback(() => {
    if (!bookmarks.length) return;
    const i = bookmarks.findIndex((b) => b.t === at);
    setAt(bookmarks[(i + 1) % bookmarks.length].t);
  }, [bookmarks, at, setAt]);

  return (
    <ClockCtx.Provider value={{ at, setAt, playing, setPlaying, step, meta: meta.data, markers, bookmarks, nextBookmark }}>
      {children}
    </ClockCtx.Provider>
  );
}

export const useClock = () => useContext(ClockCtx);
