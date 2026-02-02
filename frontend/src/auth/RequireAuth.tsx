// src/auth/RequireAuth.tsx
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { isLoggedIn } from "./tokenStore";

export default function RequireAuth() {
  const location = useLocation();

  if (!isLoggedIn()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
