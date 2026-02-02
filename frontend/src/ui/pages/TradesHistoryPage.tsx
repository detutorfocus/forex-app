import { useQuery } from "@tanstack/react-query";
import api from "../../services/api";

export default function TradesHistoryPage() {
  const historyQuery = useQuery({
    queryKey: ["trade-history"],
    queryFn: async () => {
      const res = await api.get("/trading/history/");
      return res.data;
    },
  });
export async function fetchLivePositions(){
    return apiGet("/trading/live/positions/");
    }

  if (historyQuery.isLoading) return <div>Loading...</div>;
  if (historyQuery.isError) return <div>Error loading history</div>;

  const data = historyQuery.data;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Trade History</h2>

      {/* temporary: show raw response */}
      <pre className="text-sm overflow-auto">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

