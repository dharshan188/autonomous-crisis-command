import { useState, useEffect } from "react";
import {
  submitCrisis,
  getCrisisStatus,
  getCrisisReport
} from "../services/api";

function NewCrisis() {

  // ============================
  // MODE STATE
  // ============================

  const [mode, setMode] = useState("manual"); // manual | autonomous

  // ============================
  // MANUAL STATE
  // ============================

  const [crisisText, setCrisisText] = useState("");
  const [approved, setApproved] = useState(false);
  const [response, setResponse] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [crisisId, setCrisisId] = useState(null);

  // ============================
  // AUTONOMOUS STATE
  // ============================

  const [location, setLocation] = useState("");
  const [autoResult, setAutoResult] = useState(null);
  const [autoLoading, setAutoLoading] = useState(false);

  // ============================
  // MANUAL SUBMIT
  // ============================

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

  // ============================
  // AUTONOMOUS SCAN
  // ============================

  const scanAutonomous = async () => {

    if (!location) return;

    setAutoLoading(true);
    setAutoResult(null);

    try {

      const res = await fetch("http://127.0.0.1:8000/autonomous_scan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ location })
      });

      const data = await res.json();
      setAutoResult(data);

    } catch (err) {
      setAutoResult({
        status: "ERROR",
        message: "Autonomous scan failed"
      });
    } finally {
      setAutoLoading(false);
    }
  };

  // ============================
  // POLLING MANUAL STATUS
  // ============================

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

  const statusColor = (status) => {
    if (status === "EXECUTED") return "bg-green-600";
    if (status === "CALL_TRIGGERED") return "bg-yellow-500";
    if (status === "REJECTED") return "bg-red-600";
    return "bg-gray-600";
  };

  return (
    <div className="p-10 text-gray-200 text-base">

      {/* ================= MODE TOGGLE ================= */}

      <div className="mb-6 flex gap-4">
        <button
          onClick={() => setMode("manual")}
          className={`px-6 py-2 rounded-lg ${
            mode === "manual" ? "bg-blue-600" : "bg-gray-700"
          }`}
        >
          Manual Mode
        </button>

        <button
          onClick={() => setMode("autonomous")}
          className={`px-6 py-2 rounded-lg ${
            mode === "autonomous" ? "bg-purple-600" : "bg-gray-700"
          }`}
        >
          Autonomous Mode
        </button>
      </div>

      {/* ================= MANUAL ================= */}

      {mode === "manual" && (
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

                {report && (
                  <div className="mt-4 text-sm">
                    <div>📌 Submitted: {report.submitted_at}</div>
                    <div>📞 Approval Status: {report.approval_status}</div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* ================= AUTONOMOUS ================= */}

      {mode === "autonomous" && (
        <div className="bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-lg">

          <h3 className="text-xl font-semibold mb-6">
            Autonomous Disaster Monitoring
          </h3>

          <input
            type="text"
            placeholder="Enter location (e.g. Sydney)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full p-3 bg-gray-800 rounded-lg mb-4"
          />

          <button
            onClick={scanAutonomous}
            className="bg-purple-600 px-6 py-2 rounded-lg hover:bg-purple-700 transition"
          >
            {autoLoading ? "Scanning..." : "Scan Disaster"}
          </button>

          {autoResult && (
            <div className="mt-6 p-4 bg-gray-800 rounded-lg text-sm">
              <div className="font-bold mb-2">{autoResult.status}</div>
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(autoResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

    </div>
  );
}

export default NewCrisis;