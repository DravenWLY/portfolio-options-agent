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
import AgentTeamAnalysisPage from "./pages/AgentTeamAnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import PortfolioContextPage from "./pages/PortfolioContextPage";
import SettingsPage from "./pages/SettingsPage";
import LandingPage from "./pages/LandingPage";
import PricingPage from "./pages/PricingPage";
import AuthPage from "./pages/AuthPage";
import MarketMoodPage from "./pages/MarketMoodPage";
import AccountDetailsPage from "./pages/AccountDetailsPage";

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
              <Route path="/agent-team-analysis" element={<AgentTeamAnalysisPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/portfolio-context" element={<PortfolioContextPage />} />
              <Route path="/market-context/market-mood" element={<MarketMoodPage />} />
              <Route path="/account-details" element={<AccountDetailsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/landing" element={<LandingPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/auth" element={<AuthPage />} />
            </Routes>
          </AppShell>
        </AccountProvider>
      </UIPreferenceProvider>
    </BrowserRouter>
  );
}
