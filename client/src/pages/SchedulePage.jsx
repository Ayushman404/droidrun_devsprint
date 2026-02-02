import { useState, useEffect } from "react";
import { Calendar, Trash2, Plus, Clock, Zap, Shield, Gavel } from "lucide-react";
import * as api from "../api"; 
import AppSelector from "../components/AppSelector"; // <--- IMPORT THIS

export default function SchedulePage() {
  const [schedules, setSchedules] = useState([]);
  const [form, setForm] = useState({
    start: "09:00",
    end: "17:00",
    label: "",
    study_mode: true,
    doomscroll_mode: true,
    punishment_type: "HOME",
    punishment_target: ""
  });

  // ... loadSchedules, handleAdd, handleDelete remain same ...
  // (Paste your existing logic here)
  useEffect(() => { loadSchedules(); }, []);

  const loadSchedules = async () => {
    try {
        const res = await api.getSchedule(); 
        setSchedules(res.data);
    } catch(e) {}
  };

  const handleAdd = async () => {
    if(!form.label) return;
    try {
        await api.addSchedule(form);
        setForm({ ...form, label: "" });
        loadSchedules();
    } catch(e) {}
  };

  const handleDelete = async (id) => {
    try {
        await api.deleteSchedule(id);
        loadSchedules();
    } catch(e) {}
  };

  return (
    <div className="space-y-8 pb-10">
      <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
        <Calendar className="text-green-400" /> AUTOPILOT PROTOCOLS
      </h2>

      {/* --- ADD NEW RULE CARD --- */}
      <div className="bg-[#121212] border border-gray-800 rounded-lg p-6">
        <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase">Create New Routine</h3>
        
        {/* Time Inputs & Label (No Changes) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
            <div className="flex gap-4">
                <div className="flex-1">
                    <label className="text-[10px] text-gray-500 block mb-1">START TIME</label>
                    <input type="time" value={form.start} onChange={e => setForm({...form, start: e.target.value})} className="w-full bg-black border border-gray-700 rounded p-2 text-white" />
                </div>
                <div className="flex-1">
                    <label className="text-[10px] text-gray-500 block mb-1">END TIME</label>
                    <input type="time" value={form.end} onChange={e => setForm({...form, end: e.target.value})} className="w-full bg-black border border-gray-700 rounded p-2 text-white" />
                </div>
            </div>
            <div>
                <label className="text-[10px] text-gray-500 block mb-1">ROUTINE NAME</label>
                <input type="text" placeholder="e.g. Deep Work Morning" value={form.label} onChange={e => setForm({...form, label: e.target.value})} className="w-full bg-black border border-gray-700 rounded p-2 text-white" />
            </div>
        </div>

        {/* Config Toggles */}
        <div className="flex flex-wrap gap-4 border-t border-gray-800 pt-4 items-center">
            {/* ... Checkboxes remain same ... */}
            <label className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" checked={form.study_mode} onChange={e => setForm({...form, study_mode: e.target.checked})} className="accent-cyan-500" />
                <Zap size={14} className={form.study_mode ? "text-cyan-400" : "text-gray-600"} /> Study Mode
            </label>

            <label className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer select-none">
                <input type="checkbox" checked={form.doomscroll_mode} onChange={e => setForm({...form, doomscroll_mode: e.target.checked})} className="accent-yellow-500" />
                <Shield size={14} className={form.doomscroll_mode ? "text-yellow-400" : "text-gray-600"} /> Doomscroll Guard
            </label>
            
            {/* --- IMPROVED PUNISHMENT SELECTOR --- */}
            <div className="flex flex-col sm:flex-row items-center gap-2 ml-auto w-full sm:w-auto mt-2 sm:mt-0">
                <div className="flex items-center gap-2">
                    <Gavel size={14} className="text-red-400" />
                    <select 
                        value={form.punishment_type} 
                        onChange={e => setForm({...form, punishment_type: e.target.value})}
                        className="bg-black border border-gray-700 rounded px-2 py-2 text-xs text-white focus:outline-none"
                    >
                        <option value="HOME">Force Home</option>
                        <option value="BACK">Force Back</option>
                        <option value="OPEN_APP">Open App...</option>
                    </select>
                </div>

                {/* CONDITIONAL RENDER: Only show App Selector if "OPEN_APP" is chosen */}
                {form.punishment_type === "OPEN_APP" && (
                    <div className="w-48 animate-in fade-in slide-in-from-right-2">
                        <AppSelector 
                            value={form.punishment_target} 
                            onChange={(val) => setForm({...form, punishment_target: val})}
                        />
                    </div>
                )}
            </div>
        </div>

        <button onClick={handleAdd} className="w-full mt-4 bg-green-900/30 text-green-400 border border-green-500/30 py-2 rounded text-sm font-bold hover:bg-green-900/50 transition-all flex items-center justify-center gap-2">
            <Plus size={16} /> ADD SCHEDULE
        </button>
      </div>

      {/* --- LIST OF SCHEDULES --- */}
      <div className="grid gap-4">
        {schedules.map(sch => (
            <div key={sch.id} className="bg-[#121212] border border-gray-800 rounded p-4 flex items-center justify-between group hover:border-gray-600 transition-all">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <Clock size={16} className="text-gray-500" />
                        <span className="font-mono text-lg text-white">{sch.start_time.substring(0,5)} - {sch.end_time.substring(0,5)}</span>
                        <span className="text-sm font-bold text-gray-400 bg-gray-900 px-2 py-0.5 rounded border border-gray-800">{sch.label}</span>
                    </div>
                    <div className="flex gap-3 text-[10px] text-gray-500">
                        {sch.study_mode && <span className="text-cyan-600 flex items-center gap-1"><Zap size={10}/> STUDY</span>}
                        {sch.doomscroll_mode && <span className="text-yellow-600 flex items-center gap-1"><Shield size={10}/> DOOM GUARD</span>}
                        
                        {/* Display the Punishment nicely */}
                        <span className="text-red-900 flex items-center gap-1">
                            <Gavel size={10}/> 
                            {sch.punishment_type === "OPEN_APP" 
                                ? `OPEN: ${sch.punishment_target.split('.').pop()}` // Clean name for display
                                : sch.punishment_type}
                        </span>
                    </div>
                </div>
                <button onClick={() => handleDelete(sch.id)} className="text-gray-600 hover:text-red-500 transition-colors">
                    <Trash2 size={18} />
                </button>
            </div>
        ))}
        {schedules.length === 0 && (
            <div className="text-center py-10 text-gray-600 text-sm">NO ACTIVE SCHEDULES</div>
        )}
      </div>
    </div>
  );
}