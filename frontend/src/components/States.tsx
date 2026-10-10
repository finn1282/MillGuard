import { useLang } from "../lib/i18n";

export function Loading() {
  const { t } = useLang();
  return <div role="status" className="p-6 text-muted text-lg animate-pulse">{t("loading")}</div>;
}

export function ErrorBox({ error, retry }: { error?: Error; retry?: () => void }) {
  const { t } = useLang();
  return (
    <div role="alert" className="m-4 lg:m-10 bg-card border border-rule rounded p-5 flex flex-wrap items-center gap-4">
      <div className="flex-1 min-w-0">
        <p className="m-0 font-bold text-lg">{t("error")}</p>
        {error && <p className="m-0 text-muted font-num text-sm break-words">{error.message}</p>}
      </div>
      {retry && <button className="btn btn-outline" onClick={retry}>{t("retry")}</button>}
    </div>
  );
}

export function Empty({ text }: { text?: string }) {
  const { t } = useLang();
  return <p className="p-6 text-muted text-lg">{text ?? t("empty")}</p>;
}
