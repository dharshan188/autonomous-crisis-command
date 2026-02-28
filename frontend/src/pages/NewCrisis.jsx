import { useState, useEffect } from "react";
import {
  submitCrisis,
  getCrisisStatus,
  getCrisisReport
} from "../services/api";

function NewCrisis() {

  const [crisisText, setCrisisText] = useState("");
  const [approved, setApproved] = useState(false);
  const [response, setResponse] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [crisisId, setCrisisId] = useState(null);

  // -----------------------------
  // Submit Crisis
  // -----------------------------

  const sendCrisis = async () => {

    if (!crisisText) return;

    setLoading(true);
    setResponse(null);
    setReport(null);
    setError(null);
    setCrisisId(null);

    try {
      const data = await submitCrisis(crisisText, approved);
      setResponse(data);

      if (data.crisis_id) {
        setCrisisId(data.crisis_id);
      }

    } catch (err) {
      setError(err?.message || "Request failed");
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------
  // Poll Status
  // -----------------------------

  useEffect(() => {

    if (!crisisId) return;

    const interval = setInterval(async () => {

      try {

        const status = await getCrisisStatus(crisisId);

        if (
          status.status === "EXECUTED" ||
          status.status === "REJECTED"
        ) {
          setResponse(status);

          // fetch full report
          const fullReport = await getCrisisReport(crisisId);
          setReport(fullReport);

          clearInterval(interval);
        }

      } catch (err) {
        console.error("Polling error:", err);
      }

    }, 3000);

    return () => clearInterval(interval);

  }, [crisisId]);

  // -----------------------------
  // UI Color
  // -----------------------------

  const statusColor = (status) => {
    if (status === "EXECUTED") return "bg-green-600";
    if (status === "CALL_TRIGGERED" || status === "WAITING_APPROVAL")
      return "bg-yellow-500";
    if (status === "REJECTED") return "bg-red-600";
    return "bg-gray-600";
  };

  return (
    <div className="p-10 text-gray-200 text-base">

      <div className="grid grid-cols-2 gap-8">

        {/* LEFT PANEL */}

        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">

          <h3 className="font-semibold mb-4 text-xl text-white">
            Crisis Deployment Interface
          </h3>

          <textarea
            className="w-full p-3 bg-gray-800 rounded-lg mb-4 text-white"
            rows="5"
            placeholder="Describe the crisis situation..."
            value={crisisText}
            onChange={(e) => setCrisisText(e.target.value)}
          />

          <div className="flex justify-between items-center">

            <label className="flex items-center gap-2 text-gray-300">
              <input
                type="checkbox"
                checked={approved}
                onChange={() => setApproved(!approved)}
              />
              Executive Pre-Authorization Enabled
            </label>

            <button
              onClick={sendCrisis}
              className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              {loading ? "Processing..." : "Execute AI Resolution"}
            </button>

          </div>
        </div>

        {/* RIGHT PANEL */}

        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">

          <h3 className="font-semibold mb-4 text-xl text-white">
            Live Crisis Report
          </h3>

          {!response && <p className="text-gray-500">Awaiting input...</p>}

          {response && (
            <>
              <div className="mb-4">
                <span className={`px-4 py-1 rounded-full font-bold ${statusColor(response.status)}`}>
                  {response.status}
                </span>
              </div>

              {crisisId && (
                <div className="text-sm text-gray-400">
                  Crisis ID: {crisisId}
                </div>
              )}

              {/* Timeline Section */}

              {report && (
                <div className="mt-4 text-sm">

                  <div>📌 Submitted: {report.submitted_at}</div>
                  <div>📞 Approval Status: {report.approval_status}</div>
                  {report.approval_time && (
                    <div>✅ Approval Time: {report.approval_time}</div>
                  )}
                  {report.dispatch_time && (
                    <div>🚒 Dispatch Time: {report.dispatch_time}</div>
                  )}

                  {report.teams_notified?.length > 0 && (
                    <div className="mt-2">
                      <div className="font-semibold">Teams Notified:</div>
                      {report.teams_notified.map((team, i) => (
                        <div key={i}>
                          🔔 {team.type} at {team.location} ({team.time})
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Download PDF */}

                  <a
                    href={`http://127.0.0.1:8000/download_report/${crisisId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-4 bg-green-600 px-4 py-2 rounded-lg"
                  >
                    Download PDF Report
                  </a>

                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
}

export default NewCrisis;