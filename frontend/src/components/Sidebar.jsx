import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <div className="w-64 bg-gray-900 min-h-screen p-6 border-r border-gray-800">
      
      <div className="mb-10">
        <h2 className="text-xl font-bold">Crisis Command</h2>
        <p className="text-xs text-gray-400 mt-1">
          SAP Hackathon 2026
        </p>
      </div>

      <nav className="flex flex-col gap-4 text-gray-300 text-sm">
        <Link to="/" className="hover:text-white">
          Crisis Deployment
        </Link>
        <Link to="/live-monitor" className="hover:text-white">
          Live Operations
        </Link>
        <Link to="/resources" className="hover:text-white">
          Resource Management
        </Link>
        <Link to="/audit" className="hover:text-white">
          Audit & Governance
        </Link>
        <Link to="/analytics" className="hover:text-white">
          System Analytics
        </Link>
      </nav>
    </div>
  );
}

export default Sidebar;