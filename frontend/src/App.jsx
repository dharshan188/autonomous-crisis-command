import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

import NewCrisis from "./pages/NewCrisis";
import LiveMonitor from "./pages/LiveMonitor";
import Resources from "./pages/Resources";
import AuditLog from "./pages/AuditLog";
import Analytics from "./pages/Analytics";
import Operations from "./pages/Operations";
import Autonomous from "./pages/Autonomous";   // ✅ ADD THIS

function App() {
  return (
    <Router>
      <div className="flex bg-gray-950 min-h-screen text-white">

        {/* Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">

          <Topbar />

          <div className="p-6 flex-1 overflow-y-auto">
            <Routes>

              {/* Manual Crisis Page */}
              <Route path="/" element={<NewCrisis />} />

              {/* Autonomous Monitoring */}
              <Route path="/autonomous" element={<Autonomous />} />

              {/* Live Monitoring */}
              <Route path="/live-monitor" element={<LiveMonitor />} />

              {/* Resource Registry */}
              <Route path="/resources" element={<Resources />} />

              {/* Audit Logs */}
              <Route path="/audit" element={<AuditLog />} />

              {/* Analytics Dashboard */}
              <Route path="/analytics" element={<Analytics />} />

              {/* Operations Dashboard */}
              <Route path="/operations" element={<Operations />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" />} />

            </Routes>
          </div>

        </div>
      </div>
    </Router>
  );
}

export default App;