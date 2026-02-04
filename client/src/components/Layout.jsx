import { Link, useLocation } from "react-router-dom";
import { ShieldAlert, Activity, Grid, Settings, PieChart, LayoutDashboard, Calendar } from "lucide-react";

export default function Layout({ children }) {
  const { pathname } = useLocation();

  const NavItem = ({ to, icon: Icon, label }) => {
    const active = pathname === to;
    return (
      <Link
        to={to}
        className={`flex items-center gap-3 px-4 py-3 rounded-r-lg transition-all border-l-4 ${
          active
            ? "border-cyan-400 bg-white/5 text-cyan-400"
            : "border-transparent text-gray-500 hover:text-gray-300 hover:bg-white/5"
        }`}
      >
        <Icon size={20} />
        <span className="font-mono text-sm tracking-wider">{label}</span>
      </Link>
    );
  };

  return (
    <div className="flex min-h-screen bg-[#050505] text-gray-200 font-mono">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-800 flex flex-col fixed h-full bg-[#050505] z-10">
        <div className="h-16 flex items-center px-6 border-b border-gray-800">
          <ShieldAlert className="text-cyan-400 mr-3" />
          <span className="font-bold text-lg tracking-widest text-white">PARENTAL DASHBOARD</span>
        </div>
        
        <nav className="flex-1 py-6 space-y-2 pr-4">
            <NavItem to="/" icon={LayoutDashboard} label="DASHBOARD" />
            <NavItem to="/apps" icon={Grid} label="APP RULES" />
            <NavItem to="/analytics" icon={PieChart} label="ANALYTICS" /> {/* New Link */}
            <NavItem to="/settings" icon={Settings} label="SYSTEM" />
            <NavItem to="/schedule" icon={Calendar} label="Autopilot" />
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-2 text-xs text-green-500">
            <Activity size={14} className="animate-pulse" />
            ONLINE
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}