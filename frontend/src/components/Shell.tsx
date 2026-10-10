import { useEffect } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useClock } from "../lib/clock";
import { useLang, type Key } from "../lib/i18n";
import { ErrorBoundary } from "./ErrorBoundary";
import { TimeBar } from "./TimeBar";

export const PAGES: { to: string; key: Key }[] = [
  { to: "/mill", key: "mill" },
  { to: "/machine", key: "machine" },
  { to: "/impact", key: "impact" },
  { to: "/how", key: "how" },
];

function Rail() {
  const { t } = useLang();
  return (
    <nav aria-label="Main" className="hidden lg:flex flex-col gap-1 w-[212px] flex-none bg-navy text-paper px-3.5 py-6 sticky top-0 h-screen">
      <div className="font-extrabold text-xl tracking-wider px-3 pb-7">MILLGUARD</div>
      {PAGES.map((p, i) => (
        <NavLink key={p.to} to={p.to}
          className={({ isActive }) => `flex items-center gap-3 p-3 rounded min-h-[48px] text-[17px] no-underline
            ${isActive ? "bg-paper text-ink font-bold" : "text-db-label hover:bg-navy-2"}`}>
          {({ isActive }) => (<>
            <span className={`font-num text-sm ${isActive ? "text-muted" : "text-db-num"}`}>0{i + 1}</span>{t(p.key)}
          </>)}
        </NavLink>
      ))}
    </nav>
  );
}

function Tabs() {
  const { t } = useLang();
  return (
    <nav aria-label="Main" className="lg:hidden fixed bottom-0 inset-x-0 z-30 bg-navy grid grid-cols-4 gap-1 px-2 pt-2 pb-[max(12px,env(safe-area-inset-bottom))]">
      {PAGES.map((p, i) => (
        <NavLink key={p.to} to={p.to}
          className={({ isActive }) => `flex flex-col items-center justify-center gap-0.5 min-h-[48px] rounded px-0.5 py-1 text-xs text-center leading-tight no-underline
            ${isActive ? "bg-paper text-ink font-bold" : "text-db-label"}`}>
          {({ isActive }) => (<>
            <span className={`font-num text-[11px] ${isActive ? "text-muted" : "text-db-num"}`}>0{i + 1}</span>{t(p.key)}
          </>)}
        </NavLink>
      ))}
    </nav>
  );
}

// Presenter shortcuts: 1-4 switch pages, B jumps to the next bookmark.
function useShortcuts() {
  const nav = useNavigate();
  const { nextBookmark } = useClock();
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      if (e.metaKey || e.ctrlKey || e.altKey || el.closest("input, textarea, select, [contenteditable]")) return;
      const i = Number(e.key) - 1;
      if (i >= 0 && i < PAGES.length) nav(PAGES[i].to);
      else if (e.key === "b" || e.key === "B") nextBookmark();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [nav, nextBookmark]);
}

export function Shell() {
  useShortcuts();
  const { pathname } = useLocation();
  const clocked = /^\/(mill|machine)/.test(pathname);
  return (
    <div className="min-h-screen bg-paper text-ink font-ui lg:flex">
      <Rail />
      <main className="flex-1 min-w-0 flex flex-col pb-[var(--tabbar-h)] lg:pb-0">
        {clocked && <TimeBar />}
        <ErrorBoundary resetKey={pathname}><Outlet /></ErrorBoundary>
      </main>
      <Tabs />
    </div>
  );
}
