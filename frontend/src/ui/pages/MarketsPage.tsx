import { Card } from "../components/Card";

export default function MarketsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Markets</h1>
      <Card>
        <p className="opacity-80">
          Coming next: live price tiles and a watchlist. For now, use the
          Dashboard watchlist.
        </p>
      </Card>
    </div>
  );
}
