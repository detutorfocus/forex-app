import React from "react";
import { Link, useLocation } from "react-router-dom";

type LocationState = { email?: string };

export default function ResetSent() {
  const loc = useLocation();
  const email = (loc.state as LocationState | null)?.email;

  return (
    <div style={{ maxWidth: 560, margin: "40px auto", display: "grid", gap: 12 }}>
      <h2>Check your email</h2>

      <p>
        If that email is registered, a reset link has been sent{email ? <> to <b>{email}</b></> : null}.
      </p>

      <ul style={{ margin: 0, paddingLeft: 18, opacity: 0.9 }}>
        <li>Check spam or promotions.</li>
        <li>Make sure the email address is correct.</li>
        <li>Delivery can take a minute.</li>
      </ul>

      <Link to="/auth/login">Back to login</Link>
    </div>
  );
}
