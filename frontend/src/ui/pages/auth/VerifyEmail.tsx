import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthAPI } from "../../api/auth";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const key = params.get("key");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState<string>("Confirming your email…");

  useEffect(() => {
    let alive = true;

    const run = async () => {
      if (!key) {
        setStatus("error");
        setMessage("This link is missing information.");
        return;
      }

      try {
        await AuthAPI.verifyEmail(key);
        if (!alive) return;
        setStatus("success");
        setMessage("Email confirmed. Redirecting to login…");
        setTimeout(() => nav("/auth/login"), 1200);
      } catch {
        if (!alive) return;
        setStatus("error");
        setMessage("This link is invalid or has expired.");
      }
    };

    run();
    return () => {
      alive = false;
    };
  }, [key, nav]);

  return (
    <div style={{ maxWidth: 560, margin: "40px auto", display: "grid", gap: 12 }}>
      <h2>Confirm email</h2>

      <p style={{ color: status === "error" ? "crimson" : undefined }}>{message}</p>

      {status === "error" && (
        <div style={{ display: "flex", gap: 12 }}>
          <Link to="/auth/check-email">Send a new link</Link>
          <Link to="/auth/login">Back to login</Link>
        </div>
      )}
    </div>
  );
}
