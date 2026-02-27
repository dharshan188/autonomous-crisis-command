import { useEffect, useState } from "react";

function AuditLog() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/audit")
      .then(res => res.json())
      .then(data => setLogs(data))
      .catch(() => {});
  }, []);

  return (
    <div className="p-8 text-gray-200">
      <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>

      <div className="bg-gray-800 p-6 rounded-xl">
        {logs.length === 0 && <p>No logs available.</p>}
        {logs.map((log, index) => (
          <pre key={index} className="text-sm mb-4">
            {JSON.stringify(log, null, 2)}
          </pre>
        ))}
      </div>
    </div>
  );
}

export default AuditLog;