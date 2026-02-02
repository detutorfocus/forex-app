import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import { clearAuth } from "../../services/auth";
import { logout } from "../auth/logout"; // adjust path
import Button from "../ui/components/Button"; // adjust path
import {
  LayoutGrid,
  LineChart,
  Newspaper,
  Settings,
  Bot,
  ListOrdered,
  User,
  CreditCard,
  LifeBuoy,
  Info,
  LogOut,
  XCircle,
} from "lucide-react";
import { emergencyCloseAll } from "../../services/tradingHistory";

const topLinks = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/markets", label: "Markets" },
  { to: "/news", label: "News" },
  { to: "/settings", label: "Settings" },
];

const sideLinks = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutGrid },
  { to: "/trades", label: "Trades", icon: ListOrdered },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/audit", label: "Audit", icon: LineChart },
  { to: "/profile", label: "Profile", icon: User },
  { to: "/accounts", label: "Accounts", icon: CreditCard },
  { to: "/support", label: "Support", icon: LifeBuoy },
  { to: "/about", label: "About", icon: Info },
];

function LinkPill({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "px-3 py-1.5 rounded-xl text-sm transition",
          isActive
            ? "bg-white/10 text-white"
            : "text-white/70 hover:text-white hover:bg-white/5",
        ].join(" ")
      }
    >
      {label}
    </NavLink>
  );
}

function IconLink({ to, label, Icon }: { to: string; label: string; Icon: any }) {
  return (
    <NavLink
      to={to}
      title={label}
      className={({ isActive }) =>
        [
          "h-11 w-11 grid place-items-center rounded-2xl transition",
          isActive
            ? "bg-white/10 text-white"
            : "text-white/70 hover:text-white hover:bg-white/5",
        ].join(" ")
      }
    >
      <Icon className="h-5 w-5" />
    </NavLink>
  );
}

export default function AppLayout() {
  const nav = useNavigate();
  const [busyClose, setBusyClose] = useState(false);

  const onLogout = () => {
    clearAuth();
    nav("/login", { replace: true });
  };

  const onEmergencyClose = async () => {
    if (busyClose) return;
    setBusyClose(true);
    try {
      await emergencyCloseAll();
      // keep UX trader-friendly (no raw JSON)
      alert("Emergency close sent. If the market is open, positions will be closed.");
    } catch {
      alert("Could not send the close request. Please try again.");
    } finally {
      setBusyClose(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1020] text-white">
      {/* subtle vignette to match screenshot feel */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_center,rgba(255,255,255,0.08),rgba(0,0,0,0))]" />

      <div className="relative mx-auto max-w-[1400px] px-6 py-6">
        <div className="flex gap-6">
          {/* Sidebar */}
          <aside className="w-16 shrink-0">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-2 backdrop-blur">
              <div className="h-10 w-10 mx-auto rounded-2xl bg-white/10 grid place-items-center mb-3">
                <span className="text-xs font-semibold">NT</span>
              </div>
              <nav className="grid gap-2">
                {sideLinks.map((l) => (
                  <IconLink
                    key={l.to}
                    to={l.to}
                    label={l.label}
                    Icon={l.icon}
                  />
                ))}
              </nav>
            </div>
          </aside>

          {/* Main */}
          <main className="flex-1">
            {/* Top bar */}
            <header className="flex items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-2">
                <span className="text-white/60 text-sm">NexaTrade</span>
              </div>

              <div className="flex items-center gap-2">
                {topLinks.map((l) => (
                  <LinkPill key={l.to} to={l.to} label={l.label} />
                ))}
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={onEmergencyClose}
                  disabled={busyClose}
                  className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm bg-emerald-600/80 hover:bg-emerald-600 transition disabled:opacity-50"
                >
                  <XCircle className="h-4 w-4" />
                  Emergency close
                </button>
                <button
                  onClick={onLogout}
                  className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm bg-blue-600/80 hover:bg-blue-600 transition"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            </header>

            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
