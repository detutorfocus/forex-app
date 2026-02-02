import React, { useMemo, useState } from "react";
import { AuthAPI } from "../../api/auth";

type Props = {
  email?: string;
  cooldownSeconds?: number;
};

export default function ResendEmailButton({ email, cooldownSeconds = 60 }: Props) {
  const [remaining, setRemaining] = useState<number>(0);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");

  const disabled = useMemo(() => !email || remaining > 0 || status === "loading", [email, remaining, status]);

  const startCooldown = () => {
    setRemaining(cooldownSeconds);
    const interval = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(interval);
          return 0;
        }
        return r - 1;
      });
    }, 1000);
  };

  const resend = async () => {
    if (!email) return;
    setStatus("loading");
    try {
      await AuthAPI.resendVerification(email);
      setStatus("success");
      startCooldown();
    } catch {
      setStatus("error");
    }
  };

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <button onClick={resend} disabled={disabled}>
        {status === "loading" ? "Sending…" : remaining > 0 ? `Resend in ${remaining}s` : "Resend email"}
      </button>

      {status === "success" && <div style={{ fontSize: 14, opacity: 0.9 }}>New email sent.</div>}
      {status === "error" && (
        <div style={{ fontSize: 14, color: "crimson" }}>Couldn’t send right now. Try again shortly.</div>
      )}
    </div>
  );
}
