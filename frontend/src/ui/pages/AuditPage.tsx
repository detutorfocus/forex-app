import { useState } from "react";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { auditExport, auditVerify } from "../../services/trading";

export default function AuditPage() {
  const [busy, setBusy] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function downloadCsv() {
    setBusy(true);
    setError(null);
    try {
      const blob = (await auditExport("csv")) as Blob;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit_export.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || "CSV export failed. Confirm backend supports ?format=csv");
    } finally {
      setBusy(false);
    }
  }

  async function downloadJson() {
    setBusy(true);
    setError(null);
    try {
      const data = await auditExport("json");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "audit_export.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || "JSON export failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Audit</h2>
        <div className="text-sm text-slate-400">
          Export and verify your tamper-evident audit chain.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card
          title="Export"
          right={
            <div className="flex gap-2">
              <Button variant="secondary" disabled={busy} onClick={downloadCsv}>
                Download CSV
              </Button>
              <Button variant="secondary" disabled={busy} onClick={downloadJson}>
                Download JSON
              </Button>
            </div>
          }
        >
          <div className="text-sm text-slate-300">
            Uses <span className="text-slate-200">/audit/export?format=csv|json</span>.
          </div>
          {error && <div className="mt-3 text-sm text-rose-300">{error}</div>}
        </Card>

        <Card title="Verify chain">
          <div className="text-sm text-slate-300">
            Runs backend verification and returns status.
          </div>

          <div className="mt-4">
            <Button
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                setError(null);
                try {
                  const data = await auditVerify();
                  setVerifyResult(data);
                } catch (e: any) {
                  setError(e?.message || "Verify failed. Confirm endpoint /audit/verify/");
                } finally {
                  setBusy(false);
                }
              }}
            >
              {busy ? "Running…" : "Verify"}
            </Button>
          </div>

          {verifyResult && (
            <pre className="mt-4 text-xs rounded-xl bg-slate-950/50 border border-slate-800 p-4 overflow-auto">
{JSON.stringify(verifyResult, null, 2)}
            </pre>
          )}

          {error && <div className="mt-3 text-sm text-rose-300">{error}</div>}
        </Card>
      </div>
    </div>
  );
}
