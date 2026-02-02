import { Card } from "../components/Card";

export default function ProfilePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">User Profile</h1>
      <Card>
        <p className="opacity-80">
          Profile details and preferences will be shown here.
        </p>
      </Card>
    </div>
  );
}
