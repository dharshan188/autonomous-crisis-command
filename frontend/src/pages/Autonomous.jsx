import { useState, useEffect } from "react";
import axios from "axios";

function Autonomous() {

  const [location, setLocation] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [monitoring, setMonitoring] = useState(false);

  const API = "http://127.0.0.1:8000";

  // ================================
  // START MONITORING
  // ================================

  const startMonitoring = async () => {

    if (!location) return;

    setMonitoring(true);
    setLoading(true);

    try {
      const res = await axios.post(`${API}/autonomous_scan`, {
        location
      });
      setData(res.data);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
  };

  // ================================
  // POLLING EVERY 10 SECONDS
  // ================================

  useEffect(() => {

    if (!monitoring) return;

    const interval = setInterval(async () => {

      try {
        const res = await axios.post(`${API}/autonomous_scan`, {
          location
        });
        setData(res.data);
      } catch (err) {
        console.error(err);
      }

    }, 10000);

    return () => clearInterval(interval);

  }, [monitoring, location]);

  // ================================
  // STATUS COLOR
  // ================================

  const statusColor = (status) => {
    if (status === "SAFE") return "bg-green-600";
    if (status === "MONITORING") return "bg-yellow-500";
    if (status === "FLOOD_CALL_TRIGGERED") return "bg-red-600";
    if (status === "ALREADY_PENDING") return "bg-orange-500";
    return "bg-gray-600";
  };

  return (
    <div className="p-10 text-gray-200">

      <div className="grid grid-cols-2 gap-8">

        {/* LEFT PANEL */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800">

          <h3 className="text-xl font-semibold mb-4">
            Autonomous Flood Monitoring
          </h3>

          <input
            type="text"
            placeholder="Enter city or state (e.g., Sydney)"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full p-3 mb-4 bg-gray-800 rounded-lg"
          />

          <button
            onClick={startMonitoring}
            className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            {loading ? "Scanning..." : "Start Monitoring"}
          </button>

        </div>

        {/* RIGHT PANEL */}
        <div className="bg-gray-900 p-6 rounded-2xl border border-gray-800">

          <h3 className="text-xl font-semibold mb-4">
            Live Status
          </h3>

          {!data && (
            <p className="text-gray-500">
              Waiting for monitoring to begin...
            </p>
          )}

          {data && (
            <>
              {/* STATUS BADGE */}
              <div className="mb-4">
                <span className={`px-4 py-1 rounded-full font-bold ${statusColor(data.status)}`}>
                  {data.status}
                </span>
              </div>

              {/* LOCATION */}
              {data.location && (
                <div className="mb-2">
                  📍 <strong>Location:</strong> {data.location}
                </div>
              )}

              {/* WEATHER */}
              {data.weather && (
                <div className="mt-3 text-sm bg-gray-800 p-4 rounded-lg">
                  <div>🌡 Temp: {data.weather.temperature ?? "--"}°C</div>
                  <div>💧 Humidity: {data.weather.humidity ?? "--"}%</div>
                  <div>🌧 Rain (1h): {data.weather.rain_1h ?? 0} mm</div>
                  <div>🌬 Wind: {data.weather.wind_speed ?? "--"} m/s</div>
                </div>
              )}

              {/* FLOOD ALERT MESSAGE */}
              {data.status === "FLOOD_CALL_TRIGGERED" && (
                <div className="mt-4 text-red-400 font-semibold">
                  🚨 Approval Call Triggered — Awaiting Officer Response
                </div>
              )}

              {data.status === "SAFE" && (
                <div className="mt-4 text-green-400">
                  🟢 Area is Safe — Continuous Monitoring Active
                </div>
              )}

              {data.status === "MONITORING" && (
                <div className="mt-4 text-yellow-400">
                  ⚠ News Found — Monitoring Weather Conditions
                </div>
              )}

              {data.status === "ALREADY_PENDING" && (
                <div className="mt-4 text-orange-400">
                  ⏳ Flood already under approval process
                </div>
              )}

              {/* ========================= */}
              {/* NEWS SOURCES (ONLY 2) */}
              {/* ========================= */}

              {data.sources && data.sources.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold mb-2">
                    📰 News Sources ({data.news_count || data.sources.length})
                  </h4>

                  {data.sources.slice(0, 2).map((source, index) => (
                    <div
                      key={index}
                      className="mb-3 bg-gray-800 p-3 rounded-lg border border-gray-700"
                    >
                      <a
                        href={source.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline text-sm"
                      >
                        {source.title}
                      </a>
                    </div>
                  ))}
                </div>
              )}

            </>
          )}

        </div>
      </div>
    </div>
  );
}

export default Autonomous;