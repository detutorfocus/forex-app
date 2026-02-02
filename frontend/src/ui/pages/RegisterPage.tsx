import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Input } from "../components/Input";
import  { auth }  from "../../services/auth";
import { register } from "../api/auth";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-slate-900/60 border border-slate-800 p-6">
        <h1 className="text-xl font-semibold">Create account</h1>
        <p className="mt-1 text-sm text-slate-400">Register via DRF.</p>

        <div className="mt-6 space-y-4">
          <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
          <Input label="Email (optional)" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <Input label="Confirm password" type="password" value={password2} onChange={(e) => setPassword2(e.target.value)} />
        </div>

        {error && <div className="mt-4 text-sm text-rose-300">{error}</div>}

        <div className="mt-6 flex items-center justify-between">
          <Link className="text-sm text-slate-300 hover:text-white" to="/login">
            Back to login
          </Link>
          <Button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              setError(null);
              try {
                await auth.register({ username, email, password, password2 });
                navigate("/login");
              } catch (e: any) {
                setError(e?.response?.data ? JSON.stringify(e.response.data) : (e?.message ?? "Register failed"));
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Creating..." : "Create"}
          </Button>
        </div>
      </div>
    </div>
  );
}
