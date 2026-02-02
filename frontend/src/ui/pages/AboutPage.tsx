import { Card } from "../components/Card";

export default function AboutPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">About NexaTrade</h1>
      <Card>
        <p className="opacity-80">
          NexaTrade helps traders analyze, manage, and track positions with a
          clean, modern workflow.
        </p>
      </Card>
    </div>
  );
}
