import { api, USE_FIXTURES } from "./api";
import { useLang, isKey } from "./i18n";
import type { Scenario } from "./types";
import { useApi } from "./useApi";

// "scenario:bearing_p3" -> scenario id; "csv:mydata" -> "csv_mydata" (the scenario the upload built).
export const scenarioId = (source: string | null | undefined) =>
  !source ? null : source.startsWith("scenario:") ? source.slice(9) : source.startsWith("csv:") ? `csv_${source.slice(4)}` : source;

export function useScenarios() {
  return useApi<Scenario[]>(USE_FIXTURES ? null : api.scenarios, []);
}

// Display name of the live session's source, in the current language.
export function useSourceName(source: string | null | undefined): string {
  const { pick } = useLang();
  const list = useScenarios().data;
  const id = scenarioId(source);
  const s = list?.find((x) => x.id === id);
  return s ? pick(s, "name") : (id ?? "");
}

export function useSensorName() {
  const { t } = useLang();
  return (signal: string) => { const k = `sig_${signal}`; return isKey(k) ? t(k) : `${signal} ${t("sensorGeneric")}`; };
}
