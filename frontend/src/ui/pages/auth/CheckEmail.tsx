import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import ResendEmailButton from "../../components/auth/ResendEmailButton";

type LocationState = { email?: string };

export default function CheckEmail() {
  const loc = useLocation();
  const nav = useNavigate();
  const email = (loc.state as LocationState | null)?.email || "";

  return (
    <div style={{ maxWidth: 560, margin: "40px auto", display: "grid", gap: 14 }}>
      <h2>Confirm your email</h2>

      <div>
        We sent a confirmation link to <b>{email || "your email"}</b>.
      </div>

      <ul style={{ margin: 0, paddingLeft: 18, opacity: 0.9 }}>
        <li>Check spam or promotions.</li>
        <li>Make sure the email address is correct.</li>
        <li>Delivery can take a minute.</li>
      </ul>

      <ResendEmailButton email={email} />

      <div style={{ display: "flex", gap: 12, marginTop: 10 }}>
        <button onClick={() => nav("/auth/register", { state: { email } })}>Change email</button>
        <Link to="/auth/login">Back to login</Link>
      </div>
    </div>
  );
}
