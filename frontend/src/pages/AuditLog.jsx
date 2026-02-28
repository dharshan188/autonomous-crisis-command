import { useEffect, useState } from "react";

function AuditLog() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchLogs = () => {
      fetch("http://127.0.0.1:8000/audit_log")
        .then(res => res.json())
        .then(data => setLogs(data))
        .catch(() => { });
    };

    fetchLogs(); // initial fetch
    const interval = setInterval(fetchLogs, 2000); // live polling

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 text-gray-200">
      <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>

      <div className="bg-gray-800 p-6 rounded-xl overflow-y-auto max-h-[70vh]">
        {logs.length === 0 && <p>No logs available.</p>}
        {logs.slice().reverse().map((log, index) => (
          <div key={index} className="text-sm mb-4 border-b border-gray-700 pb-2">
            <span className="text-yellow-400 font-bold">[{log.timestamp}]</span>{" "}
            <span className="text-blue-400 font-bold">{log.event_type}</span>
            <pre className="mt-2 text-gray-300">
              {JSON.stringify(log.data, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AuditLog;