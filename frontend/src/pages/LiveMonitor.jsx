import { useEffect, useState } from "react";

function LiveMonitor() {
  const [events, setEvents] = useState([]);
  const [city, setCity] = useState("Chennai");
  const [autoData, setAutoData] = useState(null);

  // 🔹 Fetch audit log
  useEffect(() => {
    const fetchEvents = () => {
      fetch("http://127.0.0.1:8000/audit_log")
        .then(res => res.json())
        .then(data => setEvents(data))
        .catch(() => {});
    };

    fetchEvents();
    const interval = setInterval(fetchEvents, 3000);
    return () => clearInterval(interval);
  }, []);

  // 🔹 Fetch autonomous flood status
  useEffect(() => {
    const fetchAuto = () => {
      fetch("http://127.0.0.1:8000/autonomous_scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location: city })
      })
        .then(res => res.json())
        .then(data => setAutoData(data))
        .catch(() => {});
    };

    fetchAuto();
    const interval = setInterval(fetchAuto, 10000);
    return () => clearInterval(interval);
  }, [city]);

  const getStatusColor = () => {
    if (!autoData) return "bg-gray-600";
    if (autoData.status === "FLOOD_DETECTED") return "bg-red-600";
    if (autoData.status === "MONITORING") return "bg-yellow-600";
    return "bg-green-600";
  };

  return (
    <div className="p-8 text-gray-200">
      <h1 className="text-2xl font-bold mb-6">Live Operations Monitor</h1>

      {/* 🔹 City Selector */}
      <div className="mb-6">
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className="bg-gray-800 p-2 rounded text-white"
        >
          <option>Chennai</option>
          <option>Coimbatore</option>
          <option>Sydney</option>
          <option>Mumbai</option>
        </select>
      </div>

      {/* 🔹 Autonomous Status Panel */}
      {autoData && (
        <div className="mb-8 bg-gray-800 p-6 rounded-xl">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Autonomous Flood Status — {city}
            </h2>

            <span className={`px-3 py-1 text-xs rounded-full ${getStatusColor()}`}>
              {autoData.status}
            </span>
          </div>

          {/* 🌦 Weather */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>🌡 Temp: {autoData.weather?.temperature ?? "N/A"} °C</div>
            <div>💧 Humidity: {autoData.weather?.humidity ?? "N/A"} %</div>
            <div>🌬 Wind: {autoData.weather?.wind_speed ?? "N/A"} m/s</div>
            <div>🌧 Rain (1h): {autoData.weather?.rain_1h ?? 0} mm</div>
          </div>

          {/* 📰 News Sources */}
          {autoData.sources && autoData.sources.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-gray-400 mb-2">
                News Sources
              </h3>
              {autoData.sources.map((src, idx) => (
                <div key={idx} className="mb-2">
                  <a
                    href={src.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:underline text-sm"
                  >
                    {src.title}
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 🔹 Audit Log */}
      <div className="bg-gray-800 p-6 rounded-xl overflow-y-auto max-h-[60vh]">
        {events.length === 0 ? (
          <p className="text-gray-400">Waiting for live crisis events...</p>
        ) : (
          <div className="space-y-4">
            {events.slice().reverse().map((evt, idx) => (
              <div
                key={idx}
                className="bg-gray-700 p-4 rounded text-sm border-l-4 border-blue-500"
              >
                <span className="text-gray-400 text-xs block mb-1">
                  {new Date(evt.timestamp).toLocaleString()}
                </span>
                <span className="font-bold text-white tracking-wide">
                  {evt.event_type}
                </span>
                <div className="mt-2 text-gray-300 whitespace-pre-wrap">
                  {JSON.stringify(evt.data, null, 2)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveMonitor;