import { SampleBadge } from "./SampleBadge";
import { LangToggle } from "./TimeBar";

// Top bar for pages that are not tied to the replay clock (Impact, How it works).
export function PageBar({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="bg-paper-bar border-b border-rule flex items-center gap-2.5 lg:gap-3.5 px-4 lg:px-10 py-3 lg:py-3.5 min-h-[70px] lg:min-h-[77px]">
      <div className="flex-1 min-w-0">
        <div className="text-[15px] lg:text-xl font-extrabold">{title}</div>
        {sub && <div className="text-[13px] lg:text-base text-muted">{sub}</div>}
      </div>
      <SampleBadge />
      <LangToggle />
    </div>
  );
}
