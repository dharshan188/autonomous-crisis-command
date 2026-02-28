import { useEffect, useState } from "react";

function LiveMonitor() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const fetchEvents = () => {
      fetch("http://127.0.0.1:8000/audit_log")
        .then(res => res.json())
        .then(data => setEvents(data))
        .catch(() => { });
    };

    fetchEvents();
    const interval = setInterval(fetchEvents, 2000);

    return () => clearInterval(interval);
  }, []);
  return (
    <div className="p-8 text-gray-200">
      <h1 className="text-2xl font-bold mb-6">Live Operations Monitor</h1>
      <div className="bg-gray-800 p-6 rounded-xl overflow-y-auto max-h-[70vh]">
        {events.length === 0 ? (
          <p className="text-gray-400">Waiting for live crisis events...</p>
        ) : (
          <div className="space-y-4">
            {events.slice().reverse().map((evt, idx) => (
              <div key={idx} className="bg-gray-700 p-4 rounded text-sm border-l-4 border-blue-500">
                <span className="text-gray-400 text-xs block mb-1">{new Date(evt.timestamp).toLocaleString()}</span>
                <span className="font-bold text-white tracking-wide">{evt.event_type}</span>
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