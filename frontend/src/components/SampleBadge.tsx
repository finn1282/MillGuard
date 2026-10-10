import { USE_FIXTURES } from "../lib/api";
import { useLang } from "../lib/i18n";
import { IconFlask } from "./Icons";

export function SampleBadge() {
  const { t } = useLang();
  if (!USE_FIXTURES) return null;
  return (
    <span className="flex-none inline-flex items-center gap-1.5 text-[13px] md:text-base font-bold tracking-wide bg-sample-bg text-sample-ink border border-sample-border rounded-[4px] px-2 md:px-2.5 py-1.5">
      <IconFlask size={16} />{t("sample")}
    </span>
  );
}
