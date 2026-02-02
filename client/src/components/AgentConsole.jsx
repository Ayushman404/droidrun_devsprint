import { useState } from "react";
import { Send, Bot, Terminal } from "lucide-react";
import axios from "axios"; 

// Make sure your API base URL is correct (e.g., localhost:8000)
const API_URL = "http://localhost:8000"; 

export default function AgentConsole() {
  const [task, setTask] = useState("");
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  const handleExecute = async () => {
    if (!task) return;
    
    setLoading(true);
    setLogs(prev => [...prev, `> USER: ${task}`]);
    
    try {
      const res = await axios.post(`${API_URL}/agent/execute`, { prompt: task });
      
      if (res.data.status === "success") {
        setLogs(prev => [...prev, `> AGENT: ${res.data.output}`]);
      } else {
        setLogs(prev => [...prev, `> ERROR: ${res.data.output}`]);
      }
    } catch (e) {
      setLogs(prev => [...prev, `> SYSTEM FAILURE: Check Server Logs`]);
    }
    
    setLoading(false);
    setTask("");
  };

  return (
    <div className="bg-[#0f0f0f] border border-green-900/30 rounded-lg overflow-hidden mt-6 font-mono shadow-lg">
      {/* Header */}
      <div className="bg-[#1a1a1a] p-3 flex items-center justify-between border-b border-gray-800">
        <div className="flex items-center gap-2 text-green-500">
            <Bot size={18} />
            <span className="font-bold text-sm tracking-wider">Ask the agent to do something...</span>
        </div>
        <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/20" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
            <div className="w-3 h-3 rounded-full bg-green-500/20" />
        </div>
      </div>

      {/* Terminal Output */}
      <div className="p-4 h-48 overflow-y-auto bg-black text-xs space-y-2 custom-scrollbar">
        {logs.length === 0 && <span className="text-gray-700 select-none">Waiting for instructions...</span>}
        {logs.map((log, i) => (
            <div key={i} className={`${log.startsWith("> USER") ? "text-cyan-400" : "text-green-400"}`}>
                {log}
            </div>
        ))}
        {loading && (
            <div className="text-yellow-500 animate-pulse flex items-center gap-2">
                <Terminal size={12} /> PROCESSING...
            </div>
        )}
      </div>

      {/* Input Field */}
      <div className="p-2 bg-[#1a1a1a] flex gap-2 border-t border-gray-800">
        <input
            type="text"
            className="flex-1 bg-[#0f0f0f] text-gray-200 text-sm px-4 py-2 rounded focus:outline-none focus:ring-1 focus:ring-green-500 border border-gray-800"
            placeholder="e.g., 'Open YouTube and search for Calculus'"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
            disabled={loading}
        />
        <button 
            onClick={handleExecute}
            disabled={loading}
            className={`px-4 rounded transition-colors ${loading ? 'bg-gray-800 text-gray-500' : 'bg-green-700 hover:bg-green-600 text-white'}`}
        >
            <Send size={16} />
        </button>
      </div>
    </div>
  );
}