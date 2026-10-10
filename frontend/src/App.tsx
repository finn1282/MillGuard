import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { ClockProvider } from "./lib/clock";
import { LangProvider } from "./lib/i18n";
import { Impact } from "./pages/Impact";
import { Gateway } from "./pages/Gateway";
import { How } from "./pages/How";
import { Machine } from "./pages/Machine";
import { Mill } from "./pages/Mill";

export function App() {
  return (
    <LangProvider>
      <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "") || "/"}>
        <ClockProvider>
          <Routes>
            <Route element={<Shell />}>
              <Route path="/mill" element={<Mill />} />
              <Route path="/machine" element={<Machine />} />
              <Route path="/machine/:id" element={<Machine />} />
              <Route path="/impact" element={<Impact />} />
              <Route path="/how" element={<How />} />
              <Route path="/gateway" element={<Gateway />} />
              <Route path="*" element={<Navigate to="/mill" replace />} />
            </Route>
          </Routes>
        </ClockProvider>
      </BrowserRouter>
    </LangProvider>
  );
}
