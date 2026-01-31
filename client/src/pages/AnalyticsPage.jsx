import { useState, useEffect } from "react";
import { PieChart, Activity, AlertTriangle, Clock } from "lucide-react";
import * as api from "../api";

export default function AnalyticsPage() {
  const [data, setData] = useState({ total_time_mins: 0, total_strikes: 0, breakdown: [] });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2000); // Live update every 2s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
        const res = await api.getAnalytics();
        setData(res.data);
    } catch(e) { console.error(e); }
  };

  return (
    <div className="space-y-8 pb-10">
      <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
        <PieChart className="text-purple-400" /> MISSION REPORT
      </h2>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-[#121212] p-6 rounded-lg border border-gray-800 relative overflow-hidden">
            <div className="flex items-center gap-2 text-gray-400 mb-2 relative z-10">
                <Clock size={16} /> <span className="text-xs font-bold">SCREEN TIME</span>
            </div>
            <div className="text-4xl font-mono text-white relative z-10">
                {Math.floor(data.total_time_mins / 60)}h {data.total_time_mins % 60}m
            </div>
            <Activity className="absolute -right-4 -bottom-4 text-gray-800 w-32 h-32 opacity-20" />
        </div>

        <div className="bg-[#121212] p-6 rounded-lg border border-gray-800 relative overflow-hidden">
            <div className="flex items-center gap-2 text-gray-400 mb-2 relative z-10">
                <AlertTriangle size={16} className="text-red-500" /> <span className="text-xs font-bold">TOTAL STRIKES</span>
            </div>
            <div className="text-4xl font-mono text-red-500 relative z-10">
                {data.total_strikes}
            </div>
            <AlertTriangle className="absolute -right-4 -bottom-4 text-red-900 w-32 h-32 opacity-20" />
        </div>
      </div>

      {/* Breakdown Chart */}
      <div className="bg-[#121212] p-6 rounded-lg border border-gray-800">
        <h3 className="text-xs font-bold text-gray-500 mb-6 uppercase tracking-widest">Top Activity</h3>
        
        <div className="space-y-6">
            {data.breakdown.map((item, i) => (
                <div key={i}>
                    <div className="flex justify-between items-end mb-2">
                        <div>
                            <span className="text-gray-200 font-bold block">{item.name}</span>
                            <span className="text-[10px] text-gray-500 font-mono">{item.package}</span>
                        </div>
                        <div className="text-right">
                            <span className="text-cyan-400 font-mono block">{item.value}m</span>
                            {item.strikes > 0 && (
                                <span className="text-red-500 text-xs font-bold flex items-center gap-1 justify-end">
                                    <AlertTriangle size={10} /> {item.strikes} STRIKES
                                </span>
                            )}
                        </div>
                    </div>
                    
                    {/* Bar Chart Visual */}
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden flex">
                        <div 
                            className="h-full bg-cyan-500 transition-all duration-500" 
                            style={{ width: `${Math.max(5, (item.value / (data.total_time_mins || 1)) * 100)}%` }}
                        />
                         {/* Red segment for strikes visualization (symbolic) */}
                        {item.strikes > 0 && (
                            <div className="h-full bg-red-500 w-2 ml-1" />
                        )}
                    </div>
                </div>
            ))}

            {data.breakdown.length === 0 && (
                <div className="text-center text-gray-600 py-10 border border-dashed border-gray-800 rounded">
                    NO ACTIVITY DETECTED
                </div>
            )}
        </div>
      </div>
    </div>
  );
}