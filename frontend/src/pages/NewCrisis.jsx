import { useState } from "react";
import { mockCrisisCommand } from "../mockApi";

function NewCrisis() {
  const [crisisText, setCrisisText] = useState("");
  const [approved, setApproved] = useState(false);
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const sendCrisis = async () => {
    if (!crisisText) return;

    setLoading(true);
    setResponse(null);

    const data = await mockCrisisCommand(crisisText, approved);
    setResponse(data);

    setLoading(false);
  };

  const statusColor = (status) => {
    if (status === "EXECUTED") return "bg-green-600";
    if (status === "PENDING_APPROVAL") return "bg-yellow-500";
    return "bg-red-600";
  };

  return (
    <div className="p-10 text-gray-200">

      {/* HEADER WITH SAP LOGO */}
      <div className="flex justify-between items-start mb-12 border-b border-gray-800 pb-6">

        {/* Left Section */}
        <div>
          <h2 className="text-2xl font-bold text-white">
            Autonomous Crisis Command Platform
          </h2>
          <p className="text-gray-400 text-sm mt-2 max-w-2xl">
            SAP Hackathon Submission – AI-powered crisis detection,
            optimization-driven resource allocation, and autonomous
            decision orchestration system.
          </p>
        </div>

        {/* Right Section - SAP Branding */}
        <div className="flex flex-col items-end">
          <img
            src="/sap-logo.png"
            alt="SAP Logo"
            className="h-16 object-contain"
          />
          <span className="mt-2 text-white font-semibold text-sm tracking-wide">
            SAP x Great Lakes MBA HackFest
          </span>
        </div>

      </div>

      <div className="grid grid-cols-2 gap-8">

        {/* LEFT PANEL */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">
          <h3 className="font-semibold mb-4 text-white">
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
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={approved}
                onChange={() => setApproved(!approved)}
              />
              Executive Pre-Authorization Enabled
            </label>

            <button
              onClick={sendCrisis}
              className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 transition font-medium"
            >
              {loading ? "Processing..." : "Execute AI Resolution"}
            </button>
          </div>
        </div>

        {/* RIGHT PANEL */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800 shadow-lg">
          <h3 className="font-semibold mb-4 text-white">
            Decision Intelligence Output
          </h3>

          {!response && (
            <p className="text-gray-500">
              Awaiting crisis input...
            </p>
          )}

          {response && (
            <>
              <div className="mb-4">
                <span
                  className={`px-4 py-1 rounded-full text-sm font-bold ${statusColor(
                    response.status
                  )}`}
                >
                  {response.status}
                </span>
              </div>

              {response.execution_result && (
                <div className="text-green-400 text-sm">
                  Dispatch Units: {response.execution_result.dispatch_units.join(", ")}
                  <br />
                  Estimated Response Time: {response.execution_result.eta}
                </div>
              )}

              {response.alerts && (
                <ul className="mt-4 list-disc list-inside text-sm text-blue-400">
                  {response.alerts.map((alert, i) => (
                    <li key={i}>{alert}</li>
                  ))}
                </ul>
              )}

              {response.status === "PENDING_APPROVAL" && (
                <div className="text-yellow-400 mt-4 text-sm">
                  Executive authorization required before dispatch execution.
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