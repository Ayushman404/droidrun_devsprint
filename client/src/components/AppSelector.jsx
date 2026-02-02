import { useState, useEffect, useMemo } from "react";
import * as api from "../api"; 

export default function AppSelector({ value, onChange, placeholder = "Select App..." }) {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Optimization: fetch only once on mount
    const fetchApps = async () => {
      try {
        const res = await api.getApps(); // Uses existing endpoint
        // Sort alphabetically by Name for easier searching
        const sorted = res.data.sort((a, b) => 
            a.name.toLowerCase().localeCompare(b.name.toLowerCase())
        );
        setApps(sorted);
      } catch (e) {
        console.error("App fetch failed", e);
      } finally {
        setLoading(false);
      }
    };
    fetchApps();
  }, []);

  // Optimization: Memoize the options so React doesn't re-render 100 items unnecessarily
  const options = useMemo(() => {
    return apps.map((app) => (
      <option key={app.package} value={app.package}>
        {app.name} ({app.package.split('.').pop()})
      </option>
    ));
  }, [apps]);

  if (loading) return <div className="text-[10px] text-gray-500 animate-pulse">Loading apps...</div>;

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-black border border-gray-700 rounded px-3 py-2 text-xs text-white w-full focus:border-cyan-500 focus:outline-none"
    >
      <option value="">-- {placeholder} --</option>
      {options}
    </select>
  );
}