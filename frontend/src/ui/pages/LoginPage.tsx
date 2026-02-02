import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { login } from "../api/auth";
import {ACCESS_KEY, REFRESH_KEY, KEY_TOKEN} from "../../services/auth";
import { setAuthTokens } from "../../services/auth";

const API_BASE = "http://127.0.0.1:8000";


/*const access = res.data?.access;
const refresh = res.data?.refresh;*/
// const key = res.data?.key; // ONLY if backend returns it



export default function LoginPage() {
  const navigate = useNavigate();

  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault();
  setBusy(true);
  setError(null);

  try {
    const res = await axios.post(`${API_BASE}/api/token/`, {
      username: usernameOrEmail,
      password,
    });

    const access = res.data?.access;
    const refresh = res.data?.refresh;

    if (!access || !refresh) {
      throw new Error("JWT tokens not returned by backend");
    }

    setAuthTokens({ access, refresh }); // add key only if exists
// setAuthTokens({ access, refresh, key });

    // SAVE TOKENS (NOT getItem)
    localStorage.setItem("accessToken", access);
    localStorage.setItem("refreshToken", refresh);

    // only if your backend returns it
    const key = res.data?.key;
    if (key) localStorage.setItem("authKey", key);

    navigate("/dashboard");
  } catch (err: any) {
    setError(err?.response?.data?.detail ?? err?.message ?? "Login failed");
  } finally {
    setBusy(false);
  }
};
  return (
    <div style={{ maxWidth: 420, margin: "60px auto", padding: 16 }}>
      <h2 style={{ marginBottom: 8 }}>Sign in</h2>
      <p style={{ opacity: 0.8, marginTop: 0 }}>
        Use your backend credentials.
      </p>

      <form onSubmit={handleLogin}>
        <label style={{ display: "block", marginTop: 12 }}>
          Username or Email
        </label>
        <input
          value={usernameOrEmail}
          onChange={(e) => setUsernameOrEmail(e.target.value)}
          placeholder="username or email"
          autoComplete="username"
          style={{ width: "100%", padding: 10, marginTop: 6 }}
        />

        <label style={{ display: "block", marginTop: 12 }}>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="password"
          autoComplete="current-password"
          style={{ width: "100%", padding: 10, marginTop: 6 }}
        />

        {error && (
          <div style={{ marginTop: 12, color: "crimson" }}>{error}</div>
        )}

        <button
          type="submit"
          disabled={busy}
          style={{
            width: "100%",
            padding: 12,
            marginTop: 16,
            cursor: busy ? "not-allowed" : "pointer",
          }}
        >
          {busy ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <div style={{ marginTop: 14 }}>
        <span style={{ opacity: 0.8 }}>No account?</span>{" "}
        <Link to="/register">Create account</Link>
      </div>
    </div>
  );
}
