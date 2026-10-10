import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { connect } from "./lib/api";
import "./index.css";

// Waits for the startup health check, so every page reads the final data source (server or offline sample data).
function Boot() {
  const [ready, setReady] = useState(false);
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const id = setTimeout(() => setSlow(true), 400);
    connect().then(() => { clearTimeout(id); setReady(true); });
    return () => clearTimeout(id);
  }, []);
  if (ready) return <App />;
  if (!slow) return null;
  return (
    <div role="status" className="min-h-screen flex flex-col items-center justify-center gap-3 bg-paper text-ink px-4 text-center">
      <span aria-hidden className="w-10 h-10 rounded-full border-4 border-rule border-t-brand animate-spin" />
      <p className="m-0 text-xl font-extrabold">Starting the server…</p>
      <p className="m-0 text-base text-muted">Memulakan pelayan…</p>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><Boot /></React.StrictMode>);
