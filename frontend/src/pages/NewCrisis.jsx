import { useState, useEffect } from "react";
import { submitCrisis, getCrisisStatus } from "../services/api";

function NewCrisis() {
  const [crisisText, setCrisisText] = useState("");
  const [approved, setApproved] = useState(false);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [crisisId, setCrisisId] = useState(null);

  const sendCrisis = async () => {
    if (!crisisText) return;

    setLoading(true);
    setResponse(null);
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

  useEffect(() => {
    if (!crisisId) return;

    const interval = setInterval(async () => {
      try {
        const status = await getCrisisStatus(crisisId);

        if (status.status === "EXECUTED" || status.status === "REJECTED") {
          setResponse(status);
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
    if (status === "CALL_TRIGGERED" || status === "WAITING_APPROVAL")
      return "bg-yellow-500";
    if (status === "REJECTED") return "bg-red-600";
    return "bg-gray-600";
  };

  return (
    <div className="p-10 text-gray-200 text-base">
      <div className="flex justify-between items-start mb-12 border-b border-gray-800 pb-6">
        <div>
          <h2 className="text-3xl font-bold text-white">
            Autonomous Crisis Command Platform
          </h2>
          <p className="text-gray-400 text-base mt-2 max-w-2xl">
            AI-powered crisis detection and autonomous dispatch system.
          </p>
        </div>

        <div className="flex flex-col items-end">
          <img
            src="/sap-logo.png"
            alt="SAP Logo"
            className="h-16 object-contain"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        {/* LEFT */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">
          <h3 className="font-semibold mb-4 text-xl text-white">
            Crisis Deployment Interface
          </h3>

          <textarea
            className="w-full p-3 bg-gray-800 rounded-lg mb-4 text-white text-base"
            rows="5"
            placeholder="Describe the crisis situation..."
            value={crisisText}
            onChange={(e) => setCrisisText(e.target.value)}
          />

          <div className="flex justify-between items-center">
            <label className="flex items-center gap-2 text-base text-gray-300">
              <input
                type="checkbox"
                checked={approved}
                onChange={() => setApproved(!approved)}
              />
              Executive Pre-Authorization Enabled
            </label>

            <button
              onClick={sendCrisis}
              className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 transition font-medium text-base"
            >
              {loading ? "Processing..." : "Execute AI Resolution"}
            </button>
          </div>
        </div>

        {/* RIGHT */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">
          <h3 className="font-semibold mb-4 text-xl text-white">
            Decision Intelligence Output
          </h3>

          {!response && !error && (
            <p className="text-gray-500 text-base">
              Awaiting crisis input...
            </p>
          )}

          {error && (
            <div className="text-red-400 mb-4 text-base">
              Error: {error}
            </div>
          )}

          {response && (
            <>
              <div className="mb-4">
                <span
                  className={`px-4 py-1 rounded-full text-base font-bold ${statusColor(
                    response.status
                  )}`}
                >
                  {response.status}
                </span>
              </div>

              {crisisId && (
                <div className="mt-2 text-base text-gray-300">
                  Crisis ID:{" "}
                  <span className="font-mono text-white">
                    {crisisId}
                  </span>
                </div>
              )}

              {response.execution_result?.dispatch_log && (
                <div className="text-green-400 text-base mt-3">
                  {response.execution_result.dispatch_log.map((item, i) => (
                    <div key={i}>
                      🚒 {item.unit_type} dispatched to {item.destination}
                    </div>
                  ))}
                </div>
              )}

              {response.status === "CALL_TRIGGERED" && (
                <div className="text-yellow-400 mt-4 text-base">
                  Executive authorization required. Phone call initiated.
                </div>
              )}

              {response.status === "WAITING_APPROVAL" && (
                <div className="text-yellow-400 mt-4 text-base">
                  Waiting for executive approval...
                </div>
              )}

              {response.status === "REJECTED" && (
                <div className="text-red-400 mt-4 text-base">
                  Request rejected by executive.
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
