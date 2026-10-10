import { useLayoutEffect, useRef, useState } from "react";

// Sticky column that is taller than the screen: stick so its bottom stays reachable.
export function useStickyTop(gap = 24) {
  const ref = useRef<HTMLDivElement>(null);
  const [top, setTop] = useState(gap);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const fit = () => setTop(Math.min(gap, window.innerHeight - el.offsetHeight - gap));
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    window.addEventListener("resize", fit);
    fit();
    return () => { ro.disconnect(); window.removeEventListener("resize", fit); };
  }, [gap]);
  return { ref, top };
}
