import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthAPI } from "../../api/auth";

export default function ForgotPassword() {
  const nav = useNavigate();
  const [email, setEmail] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await AuthAPI.requestPasswordReset(email);
    } catch {
      // always proceed (don’t reveal account existence)
    } finally {
      setLoading(false);
      nav("/auth/reset-sent", { state: { email } });
    }
  };

  return (
    <div style={{ maxWidth: 420, margin: "40px auto" }}>
      <h2>Reset your password</h2>

      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button type="submit" disabled={loading}>
          {loading ? "Sending…" : "Send reset link"}
        </button>
      </form>
    </div>
  );
}
