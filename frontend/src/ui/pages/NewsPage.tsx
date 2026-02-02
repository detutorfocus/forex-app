import { Card } from "../components/Card";

export default function NewsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">News</h1>
      <Card>
        <p className="opacity-80">
          News feed will live here (economic calendar + market headlines).
        </p>
      </Card>
    </div>
  );
}
