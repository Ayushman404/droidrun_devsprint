import { useState, useEffect } from "react";
import { Save, Sliders, Zap, Brain, Shield, AlertTriangle, Flame, Gavel } from "lucide-react";
import * as api from "../api";

export default function SettingsPage() {
  const [config, setConfig] = useState({
    persona: "",
    focus: "",
    study_mode: false,
    doomscroll_mode: true,
    grace_period: 10,
    max_strikes: 3,
    penalty_duration: 60,
    punishment_type: "HOME",
    punishment_target: ""
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => { loadConfig(); }, []);

  const loadConfig = async () => {
    try {
      const res = await api.getConfig();
      setConfig(res.data);
    } catch (e) { console.error(e); }
  };

  const handleSave = async () => {
    setLoading(true);
    await api.updateConfig(config);
    setLoading(false);
    setMessage("SYSTEM CONFIGURATION UPDATED");
    setTimeout(() => setMessage(""), 3000);
  };

  const Toggle = ({ label, desc, active, onClick, icon: Icon, color }) => (
    <div 
        onClick={onClick}
        className={`cursor-pointer flex items-center justify-between p-4 rounded border transition-all ${
        active ? `bg-${color}-900/20 border-${color}-500` : "bg-[#121212] border-gray-800"
    }`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-full ${active ? `bg-${color}-500 text-black` : "bg-gray-800 text-gray-500"}`}>
            <Icon size={18} />
        </div>
        <div>
            <div className={`text-sm font-bold ${active ? "text-white" : "text-gray-400"}`}>{label}</div>
            <div className="text-[10px] text-gray-500">{desc}</div>
        </div>
      </div>
      <div className={`w-10 h-5 rounded-full p-0.5 transition-colors ${active ? `bg-${color}-500` : "bg-gray-700"}`}>
        <div className={`w-4 h-4 bg-white rounded-full transition-transform ${active ? "translate-x-5" : "translate-x-0"}`} />
      </div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto space-y-8 pb-10">
      <div className="flex items-center justify-between border-b border-gray-800 pb-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
          <Sliders className="text-cyan-400" /> SYSTEM PARAMETERS
        </h2>
        {message && <span className="text-xs text-green-400 font-mono animate-pulse">{message}</span>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Toggle 
            label="DOOMSCROLL GUARD" 
            desc="Blocks Shorts & Reels immediately."
            active={config.doomscroll_mode}
            color="yellow"
            icon={Flame}
            onClick={() => setConfig({...config, doomscroll_mode: !config.doomscroll_mode})}
        />
        <Toggle 
            label="STUDY MODE (STRICT)" 
            desc="LLM Analysis + Forced Doomscroll Guard."
            active={config.study_mode}
            color="cyan"
            icon={Brain}
            onClick={() => setConfig({...config, study_mode: !config.study_mode})}
        />
      </div>

      {/* AI Persona */}
      <section className="bg-[#121212] p-6 rounded-lg border border-gray-800">
        <h3 className="text-gray-400 text-xs font-bold mb-4 flex items-center gap-2">
          <Brain size={14} /> AI AGENT PERSONALITY
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">PERSONA</label>
            <input
              type="text"
              value={config.persona}
              onChange={(e) => setConfig({ ...config, persona: e.target.value })}
              className="w-full bg-black border border-gray-700 rounded px-3 py-2 text-gray-200 focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">CURRENT FOCUS</label>
            <input
              type="text"
              value={config.focus}
              onChange={(e) => setConfig({ ...config, focus: e.target.value })}
              className="w-full bg-black border border-gray-700 rounded px-3 py-2 text-gray-200 focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>
      </section>

      {/* Punishment & Thresholds */}
      <section className="bg-[#121212] p-6 rounded-lg border border-gray-800">
        <h3 className="text-gray-400 text-xs font-bold mb-4 flex items-center gap-2">
          <Gavel size={14} /> PUNISHMENT & THRESHOLDS
        </h3>
        
        <div className="grid grid-cols-2 gap-6 mb-6">
           <div>
            <label className="block text-xs text-gray-500 mb-1">GRACE PERIOD (Sec)</label>
            <div className="flex items-center gap-2">
                <input type="number" value={config.grace_period} onChange={(e) => setConfig({ ...config, grace_period: parseInt(e.target.value) })} className="w-full bg-black border border-gray-700 rounded px-3 py-2 text-gray-200 focus:border-cyan-500 focus:outline-none"/>
                <Zap size={16} className="text-yellow-500" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">PENALTY DURATION (Sec)</label>
            <div className="flex items-center gap-2">
                <input type="number" value={config.penalty_duration} onChange={(e) => setConfig({ ...config, penalty_duration: parseInt(e.target.value) })} className="w-full bg-black border border-gray-700 rounded px-3 py-2 text-gray-200 focus:border-cyan-500 focus:outline-none"/>
                <Shield size={16} className="text-red-500" />
            </div>
          </div>
        </div>

        <div className="space-y-4 pt-4 border-t border-gray-800">
            <div>
                <label className="block text-xs text-gray-500 mb-2">PUNISHMENT TYPE</label>
                <div className="grid grid-cols-3 gap-2">
                    {["HOME", "BACK", "OPEN_APP"].map(type => (
                        <button
                            key={type}
                            onClick={() => setConfig({...config, punishment_type: type})}
                            className={`py-2 text-xs font-bold rounded border ${
                                config.punishment_type === type 
                                ? "bg-red-500/20 border-red-500 text-white" 
                                : "bg-black border-gray-700 text-gray-500"
                            }`}
                        >
                            {type.replace("_", " ")}
                        </button>
                    ))}
                </div>
            </div>

            {config.punishment_type === "OPEN_APP" && (
                <div className="animate-in fade-in slide-in-from-top-2 duration-300">
                    <label className="block text-xs text-gray-500 mb-1">TARGET PACKAGE (e.g., com.duolingo)</label>
                    <input
                        type="text"
                        placeholder="com.package.name"
                        value={config.punishment_target}
                        onChange={(e) => setConfig({ ...config, punishment_target: e.target.value })}
                        className="w-full bg-black border border-red-500/50 rounded px-3 py-2 text-gray-200 focus:border-red-500 focus:outline-none"
                    />
                </div>
            )}
        </div>
      </section>

      <button
        onClick={handleSave}
        disabled={loading}
        className="w-full bg-cyan-900/20 hover:bg-cyan-900/40 text-cyan-400 border border-cyan-500/50 py-4 rounded font-bold tracking-widest flex items-center justify-center gap-3 transition-all"
      >
        <Save size={18} />
        {loading ? "SAVING..." : "COMMIT CHANGES"}
      </button>
    </div>
  );
}