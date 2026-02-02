import { Card } from "../components/Card";

export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Settings</h1>
      <Card>
        <p className="opacity-80">
          Theme, notifications, and security settings will be managed here.
        </p>
      </Card>
    </div>
  );
}
