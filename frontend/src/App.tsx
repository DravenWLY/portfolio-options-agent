import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AccountProvider } from "./context/AccountContext";
import { UIPreferenceProvider } from "./context/UIPreferenceContext";
import AppShell from "./components/layout/AppShell";
import AccountSelector from "./components/account/AccountSelector";
import DashboardPage from "./pages/DashboardPage";
import BrokerConnectionPage from "./pages/BrokerConnectionPage";

/**
 * App root.
 *
 * Routes:
 *   /        → DashboardPage (portfolio cockpit)
 *   /broker  → BrokerConnectionPage (read-only SnapTrade connection flow)
 *
 * React Router introduced in P11-T7 when a second top-level page was needed.
 */
export default function App() {
  return (
    <BrowserRouter>
      <UIPreferenceProvider>
        <AccountProvider>
          <AppShell accountSlot={<AccountSelector />}>
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/broker" element={<BrokerConnectionPage />} />
            </Routes>
          </AppShell>
        </AccountProvider>
      </UIPreferenceProvider>
    </BrowserRouter>
  );
}
