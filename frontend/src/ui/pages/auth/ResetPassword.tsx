import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { AuthAPI } from "../../api/auth";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const nav = useNavigate();

  const uid = params.get("uid");
  const token = params.get("token");

  const [p1, setP1] = useState<string>("");
  const [p2, setP2] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [msg, setMsg] = useState<{ type: "idle" | "error" | "success"; text: string }>({
    type: "idle",
    text: "",
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!uid || !token) {
      setMsg({ type: "error", text: "This link is invalid or incomplete." });
      return;
    }
    if (p1.length < 8) {
      setMsg({ type: "error", text: "Password must be at least 8 characters." });
      return;
    }
    if (p1 !== p2) {
      setMsg({ type: "error", text: "Passwords don’t match." });
      return;
    }

    setLoading(true);
    setMsg({ type: "idle", text: "" });

    try {
      await AuthAPI.confirmPasswordReset({
        uid,
        token,
        new_password1: p1,
        new_password2: p2,
      });
      setMsg({ type: "success", text: "Password updated. Redirecting to login…" });
      setTimeout(() => nav("/auth/login"), 1200);
    } catch {
      setMsg({ type: "error", text: "This link is invalid or has expired." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 560, margin: "40px auto", display: "grid", gap: 12 }}>
      <h2>Set a new password</h2>

      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <input type="password" placeholder="New password" value={p1} onChange={(e) => setP1(e.target.value)} />
        <input
          type="password"
          placeholder="Confirm new password"
          value={p2}
          onChange={(e) => setP2(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Saving…" : "Set new password"}
        </button>
      </form>

      {msg.type !== "idle" && (
        <p style={{ color: msg.type === "error" ? "crimson" : undefined }}>{msg.text}</p>
      )}

      <Link to="/auth/login">Back to login</Link>
    </div>
  );
}
