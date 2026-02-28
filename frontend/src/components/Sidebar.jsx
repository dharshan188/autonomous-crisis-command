import { Link, useLocation } from "react-router-dom";

function Sidebar() {

  const location = useLocation();

  const navItem = (path, label) => {
    const active = location.pathname === path;

    return (
      <Link
        to={path}
        className={`px-3 py-2 rounded-lg transition ${
          active
            ? "bg-blue-600 text-white"
            : "text-gray-300 hover:text-white hover:bg-gray-800"
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <div className="w-64 bg-gray-900 min-h-screen p-6 border-r border-gray-800">

      {/* Header */}
      <div className="mb-10">
        <h2 className="text-xl font-bold text-white">
          Crisis Command
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          SAP Hackathon 2026
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-3 text-sm">

        {navItem("/", "Crisis Deployment")}
        {navItem("/autonomous", "Autonomous Monitor")}   {/* ✅ NEW */}
        {navItem("/live-monitor", "Live Operations")}
        {navItem("/resources", "Resource Management")}
        {navItem("/audit", "Audit & Governance")}
        {navItem("/analytics", "System Analytics")}
        {navItem("/operations", "Operations Dashboard")}  {/* ✅ If used */}

      </nav>

    </div>
  );
}

export default Sidebar;