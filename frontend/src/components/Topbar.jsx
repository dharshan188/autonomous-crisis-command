function Topbar() {
  return (
    <div className="bg-gray-900 p-4 border-b border-gray-800 flex justify-between items-center">
      
      <div>
        <h1 className="text-lg font-semibold">
          Autonomous Crisis Command Platform
        </h1>
        <p className="text-xs text-gray-400">
          SAP Hackathon Submission – Intelligent Resource Optimization Engine
        </p>
      </div>

      <div className="text-sm text-blue-400 font-semibold">
        Powered by AI + Location Intelligence
      </div>
    </div>
  );
}

export default Topbar;