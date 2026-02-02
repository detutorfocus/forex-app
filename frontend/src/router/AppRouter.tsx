import { Navigate, Route, Routes } from "react-router-dom";
import RequireAuth from "./RequireAuth";
import AuthGuard from "./auth/RequireAuth";
import AppLayout from "../ui/layout/AppLayout";

import RegisterPage from "../ui/pages/RegisterPage";
import LoginPage from "../ui/pages/LoginPage";

import DashboardPage from "../ui/pages/DashboardPage";
import TradesPage from "../ui/pages/TradesPage";
import AssistantPage from "../ui/pages/AssistantPage";
import AuditPage from "../ui/pages/AuditPage";
import MarketsPage from "../ui/pages/MarketsPage";
import NewsPage from "../ui/pages/NewsPage";
import AccountsPage from "../ui/pages/AccountsPage";
import ProfilePage from "../ui/pages/ProfilePage";
import SettingsPage from "../ui/pages/SettingsPage";
import SupportPage from "../ui/pages/SupportPage";
import AboutPage from "../ui/pages/AboutPage";

export default function AppRouter() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected app shell (sidebar/topbar) */}
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Exact links used by navbar + sidebar */}
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/markets" element={<MarketsPage />} />
          <Route path="/news" element={<NewsPage />} />
          <Route path="/settings" element={<SettingsPage />} />

          <Route path="/trades" element={<TradesPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/audit" element={<AuditPage />} />

          <Route path="/accounts" element={<AccountsPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          <Route path="/support" element={<SupportPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Route>
      </Route>

      {/* Global fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}



// pages...
// import DashboardPage ... etc
