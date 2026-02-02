import { Card } from "../components/Card";

export default function AccountsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Accounts</h1>
      <Card>
        <p className="opacity-80">
          Connect broker, manage balances, and view account history here.
        </p>
      </Card>
    </div>
  );
}
