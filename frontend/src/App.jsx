import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

import NewCrisis from "./pages/NewCrisis";
import LiveMonitor from "./pages/LiveMonitor";
import Resources from "./pages/Resources";
import AuditLog from "./pages/AuditLog";
import Analytics from "./pages/Analytics";

function App() {
  return (
    <Router>
      <div className="flex bg-gray-950 min-h-screen text-white">
        <Sidebar />
        <div className="flex-1">
          <Topbar />
          <Routes>
            <Route path="/" element={<NewCrisis />} />
            <Route path="/live-monitor" element={<LiveMonitor />} />
            <Route path="/resources" element={<Resources />} />
            <Route path="/audit" element={<AuditLog />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;