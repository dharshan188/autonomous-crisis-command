import { useEffect, useState } from "react";
import { getAllReports, getReportDownloadUrl } from "../services/api";

function Operations() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllReports();
      setReports(data || []);
    } catch (err) {
      setError(err.message || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();

    const interval = setInterval(() => {
      fetchReports();
    }, 10000); // auto-refresh every 10s

    return () => clearInterval(interval);
  }, []);

  const formatDate = (date) => {
    if (!date) return "-";
    return new Date(date).toLocaleString();
  };

  const getStatusColor = (status) => {
    if (status === "APPROVED") return "bg-green-600";
    if (status === "REJECTED") return "bg-red-600";
    return "bg-yellow-500";
  };

  return (
    <div className="p-8 text-gray-200">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-white">
          Live Operations Dashboard
        </h2>

        <button
          onClick={fetchReports}
          className="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-md border border-gray-700"
        >
          Refresh
        </button>
      </div>

      <div className="bg-gray-900 p-4 rounded-2xl border border-gray-800 shadow">
        {loading && <div className="text-gray-400">Loading reports...</div>}
        {error && <div className="text-red-400">{error}</div>}

        {!loading && !error && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700 text-sm">
              <thead>
                <tr className="text-left text-gray-400">
                  <th className="px-4 py-3">Crisis ID</th>
                  <th className="px-4 py-3">Approval Status</th>
                  <th className="px-4 py-3">Submitted</th>
                  <th className="px-4 py-3">Dispatch</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {reports.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-gray-500">
                      No reports found.
                    </td>
                  </tr>
                )}

                {reports.map((r) => (
                  <tr key={r.crisis_id} className="hover:bg-gray-800">
                    <td className="px-4 py-3 font-mono text-white truncate max-w-xs">
                      {r.crisis_id}
                    </td>

                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                          r.approval_status
                        )}`}
                      >
                        {r.approval_status}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-gray-300">
                      {formatDate(r.submitted_at)}
                    </td>

                    <td className="px-4 py-3 text-gray-300">
                      {formatDate(r.dispatch_time)}
                    </td>

                    <td className="px-4 py-3">
                      <a
                        href={getReportDownloadUrl(r.crisis_id)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-block bg-green-600 px-3 py-1 rounded-md hover:bg-green-700"
                      >
                        Download PDF
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Operations;