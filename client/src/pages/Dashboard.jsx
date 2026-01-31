import { useState, useEffect, useRef } from "react";
import { Play, Square, Activity, Terminal } from "lucide-react";
import * as api from "../api";

export default function Dashboard() {
  const [status, setStatus] = useState({ running: false, current_app: "...", last_verdict: "...", logs: [] });
  const logsEndRef = useRef(null);

  useEffect(() => {
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [status.logs]);

  const fetchStatus = async () => {
    try {
      const res = await api.getStatus();
      setStatus(res.data);
    } catch (e) { console.error(e); }
  };

  const toggleSystem = async () => {
    status.running ? await api.stopSystem() : await api.startSystem();
    fetchStatus();
  };

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatusCard 
          label="STATUS" 
          value={status.running ? "ACTIVE" : "OFFLINE"} 
          color={status.running ? "text-green-400" : "text-red-500"} 
          icon={Activity}
        />
        <StatusCard 
          label="CURRENT TARGET" 
          value={status.current_app} 
          color="text-cyan-400" 
          sub={status.last_verdict}
        />
        <div className="bg-[#121212] border border-gray-800 rounded-lg p-6 flex items-center justify-center">
          <button
            onClick={toggleSystem}
            className={`w-full py-4 rounded font-bold text-xl tracking-widest transition-all ${
              status.running 
                ? "bg-red-500/10 text-red-500 border border-red-500 hover:bg-red-500 hover:text-white"
                : "bg-cyan-500/10 text-cyan-400 border border-cyan-400 hover:bg-cyan-400 hover:text-black"
            }`}
          >
            <div className="flex items-center justify-center gap-3">
              {status.running ? <Square size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" />}
              {status.running ? "TERMINATE" : "INITIALIZE"}
            </div>
          </button>
        </div>
      </div>

      {/* Terminal Logs */}
      <div className="bg-[#0a0a0a] border border-gray-800 rounded-lg overflow-hidden flex flex-col h-[500px]">
        <div className="bg-[#121212] px-4 py-2 border-b border-gray-800 flex items-center gap-2">
          <Terminal size={16} className="text-gray-500" />
          <span className="text-xs text-gray-500 font-mono">SYSTEM_LOGS</span>
        </div>
        <div className="flex-1 p-4 overflow-y-auto font-mono text-sm space-y-1">
          {status.logs.map((log, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span>
              <span className={log.includes("🚨") ? "text-red-400" : "text-gray-300"}>
                {log}
              </span>
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}

function StatusCard({ label, value, color, sub, icon: Icon }) {
  return (
    <div className="bg-[#121212] border border-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs text-gray-500 font-bold tracking-widest">{label}</span>
        {Icon && <Icon size={16} className="text-gray-600" />}
      </div>
      <div className={`text-2xl font-bold truncate ${color}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}