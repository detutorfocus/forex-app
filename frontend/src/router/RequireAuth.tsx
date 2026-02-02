// src/router/RequireAuth.tsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { isAuthenticated } from "../services/auth";

export default function RequireAuth() {
  const location = useLocation();
  const authed = isAuthenticated();

  if (!authed) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
