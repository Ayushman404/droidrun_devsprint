import { useState, useEffect } from "react";
import { Search, Ban, Clock } from "lucide-react";
import * as api from "../api";

export default function AppsPage() {
  const [apps, setApps] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadApps();
    const interval = setInterval(loadApps, 5000); // Live sync usage
    return () => clearInterval(interval);
  }, []);

  const loadApps = async () => {
    const res = await api.getApps();
    setApps(res.data);
  };

  const handleUpdate = async (pkg, limit, blocked) => {
    // Optimistic UI
    setApps(prev => prev.map(a => a.package === pkg ? { ...a, limit_mins: limit, is_blocked: blocked } : a));
    await api.updateAppRule(pkg, { limit, blocked });
  };

  const filteredApps = apps.filter(a => 
    a.name.toLowerCase().includes(search.toLowerCase()) || 
    a.package.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      {/* Toolbar */}
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold text-white tracking-tight">APP PROTOCOLS</h2>
        <div className="relative">
          <Search className="absolute left-3 top-2.5 text-gray-600" size={18} />
          <input 
            type="text" 
            placeholder="Search targets..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-[#121212] border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-300 focus:border-cyan-500 focus:outline-none w-64"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredApps.map(app => (
          <AppCard key={app.package} app={app} onUpdate={handleUpdate} />
        ))}
      </div>
    </div>
  );
}

function AppCard({ app, onUpdate }) {
  const [limit, setLimit] = useState(app.limit_mins);
  const usagePct = Math.min((app.used_mins / app.limit_mins) * 100, 100);

  return (
    <div className={`p-4 bg-[#121212] border rounded-lg transition-all hover:border-gray-600 ${
      app.is_blocked ? "border-red-900/50 opacity-75" : "border-gray-800"
    }`}>
      <div className="flex justify-between items-start mb-4">
        <div className="overflow-hidden">
          <h3 className="font-bold text-gray-200 truncate pr-2">{app.name}</h3>
          <p className="text-[10px] text-gray-600 font-mono truncate">{app.package}</p>
        </div>
        <button
          onClick={() => onUpdate(app.package, app.limit_mins, !app.is_blocked)}
          className={`p-2 rounded transition-colors ${
            app.is_blocked ? "bg-red-500 text-white" : "bg-gray-800 text-gray-400 hover:text-white"
          }`}
        >
          <Ban size={16} />
        </button>
      </div>

      {/* Usage Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500">USAGE</span>
          <span className={usagePct > 90 ? "text-red-400" : "text-cyan-400"}>
            {app.used_mins}m / {app.limit_mins}m
          </span>
        </div>
        <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all ${usagePct > 90 ? "bg-red-500" : "bg-cyan-500"}`} 
            style={{ width: `${usagePct}%` }}
          />
        </div>
      </div>

      {/* Limit Input */}
      <div className="flex items-center gap-2 pt-3 border-t border-gray-800/50">
        <Clock size={14} className="text-gray-600" />
        <span className="text-xs text-gray-500">LIMIT:</span>
        <input
          type="number"
          className="bg-transparent border-b border-gray-700 w-12 text-center text-sm focus:border-cyan-500 focus:outline-none"
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
          onBlur={() => onUpdate(app.package, parseInt(limit), app.is_blocked)}
        />
        <span className="text-xs text-gray-600">min</span>
      </div>
    </div>
  );
}