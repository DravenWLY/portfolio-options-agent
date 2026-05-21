import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AccountProvider } from "./context/AccountContext";
import { UIPreferenceProvider } from "./context/UIPreferenceContext";
import AppShell from "./components/layout/AppShell";
import AccountSelector from "./components/account/AccountSelector";
import DashboardPage from "./pages/DashboardPage";
import BrokerConnectionPage from "./pages/BrokerConnectionPage";
import MarketDataPage from "./pages/MarketDataPage";
import RiskReviewPage from "./pages/RiskReviewPage";
import TradeReviewPage from "./pages/TradeReviewPage";

/**
 * App root.
 *
 * Routes:
 *   /            → DashboardPage (portfolio cockpit)
 *   /broker      → BrokerConnectionPage (read-only SnapTrade connection flow)
 *   /market-data → MarketDataPage (Phase 12 manual/mock market-data status)
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
              <Route path="/market-data" element={<MarketDataPage />} />
              <Route path="/risk" element={<RiskReviewPage />} />
              <Route path="/trade-review" element={<TradeReviewPage />} />
            </Routes>
          </AppShell>
        </AccountProvider>
      </UIPreferenceProvider>
    </BrowserRouter>
  );
}
