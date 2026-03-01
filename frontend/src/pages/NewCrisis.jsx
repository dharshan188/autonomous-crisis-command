import { useState, useEffect } from "react";
import {
  submitCrisis,
  getCrisisStatus,
  getCrisisReport
} from "../services/api";

function NewCrisis() {

  const [crisisText, setCrisisText] = useState("");
  const [location, setLocation] = useState("");
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

    if (!crisisText || !location) return;

    setLoading(true);
    setResponse(null);
    setReport(null);
    setError(null);
    setCrisisId(null);

    try {

      const data = await submitCrisis({
        description: crisisText,
        location: location,
        approved: approved
      });

      setResponse(data);

      if (data.crisis_id) {
        setCrisisId(data.crisis_id);
      }

    } catch (err) {
      console.error(err);
      setError("Backend not reachable. Is server running?");
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

        if (status.status === "APPROVED" ||
            status.status === "EXECUTED" ||
            status.status === "REJECTED") {

          const fullReport = await getCrisisReport(crisisId);
          setReport(fullReport);
        }

        if (status.status === "EXECUTED" ||
            status.status === "REJECTED") {
          clearInterval(interval);
        }

      } catch (err) {
        console.error("Polling error:", err);
      }

    }, 3000);

    return () => clearInterval(interval);

  }, [crisisId]);

  // -----------------------------
  // Status Colors
  // -----------------------------
  const statusColor = (status) => {
    if (status === "EXECUTED") return "bg-green-600";
    if (status === "APPROVED") return "bg-blue-600";
    if (status === "CALL_TRIGGERED" || status === "PENDING_APPROVAL")
      return "bg-yellow-500";
    if (status === "REJECTED") return "bg-red-600";
    return "bg-gray-600";
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200">

      {/* HEADER */}
      <div className="flex justify-between items-center px-10 py-6 border-b border-gray-800">
        <h2 className="text-2xl font-bold text-white">
          Crisis Command Center
        </h2>
      </div>

      {/* MAIN CONTENT */}
      <div className="p-10 grid grid-cols-2 gap-8">

        {/* LEFT PANEL */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">

          <h3 className="font-semibold mb-4 text-xl text-white">
            Crisis Deployment Interface
          </h3>

          <input
            type="text"
            placeholder="Enter precise location (Area, City)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full p-3 bg-gray-800 rounded-lg mb-4 text-white"
          />

          <textarea
            className="w-full p-3 bg-gray-800 rounded-lg mb-4 text-white"
            rows="5"
            placeholder="Describe the crisis..."
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
              Executive Pre-Authorization
            </label>

            <button
              onClick={sendCrisis}
              disabled={!crisisText || !location}
              className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
            >
              {loading ? "Processing..." : "Execute AI Resolution"}
            </button>

          </div>

          {error && (
            <div className="text-red-400 mt-3 text-sm">
              {error}
            </div>
          )}

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

              {response.details && response.details[0] && (
                <div className="mt-4 text-sm space-y-2">

                  <div>📍 Location: {response.details[0].location}</div>
                  <div>⚠ Risk Score: {response.details[0].risk_score}</div>

                  {/* 🔥 Nearby Units Section */}
                  {response.details[0].nearby_units &&
                    response.details[0].nearby_units.length > 0 && (
                    <div className="mt-4">
                      <div className="font-semibold text-white mb-2">
                        Nearby Emergency Units
                      </div>

                      {response.details[0].nearby_units.map((unit, index) => (
                        <div
                          key={index}
                          className="bg-gray-800 p-3 rounded mb-2"
                        >
                          <div className="font-medium">
                            🚨 {unit.type?.toUpperCase()}
                          </div>
                          <div>{unit.name}</div>
                          <div>📍 {unit.distance_km} km</div>
                          <div>⏱ ETA: {unit.eta_minutes} mins</div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              )}

              {report && (
                <div className="mt-6 text-sm border-t border-gray-700 pt-4">
                  <div>📌 Submitted: {report.submitted_at}</div>
                  <div>📞 Approval Status: {report.approval_status}</div>

                  {report.dispatch_time && (
                    <div>🚒 Dispatch Time: {report.dispatch_time}</div>
                  )}
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