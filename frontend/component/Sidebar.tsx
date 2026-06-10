"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  TrendingUp, 
  Lightbulb, 
  Database, 
  FileText, 
  Settings as SettingsIcon,
  Activity,
  ShieldAlert,
  LogOut,
  User
} from "lucide-react";
import { useAuth } from "./AuthProvider";

export default function Sidebar() {
  const pathname = usePathname();
  const { username, logout } = useAuth();
  
  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Trends", href: "/trends", icon: TrendingUp },
    { name: "Opportunities", href: "/opportunities", icon: Lightbulb },
    { name: "Repositories", href: "/repositories", icon: Database },
    { name: "Watchlist", href: "/watchlist", icon: ShieldAlert },
    { name: "Reports", href: "/reports", icon: FileText },
    { name: "Settings", href: "/settings", icon: SettingsIcon },
  ];

  return (
    <aside className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-zinc-800 flex items-center space-x-3">
        <div className="bg-indigo-600/20 p-2 rounded-lg border border-indigo-500/30">
          <Activity className="h-6 w-6 text-indigo-400 animate-pulse" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-zinc-100 leading-none">Radar</h1>
          <span className="text-xs text-zinc-400 font-semibold tracking-wider uppercase">Startup Intelligence</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 border border-transparent"
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive ? "text-indigo-400" : "text-zinc-400"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer / Meta info */}
      <div className="p-4 border-t border-zinc-800 space-y-3">
        {username && (
          <div className="flex items-center justify-between px-2 py-1.5 bg-zinc-900/50 rounded-lg border border-zinc-800">
            <div className="flex items-center space-x-2 overflow-hidden">
              <User className="h-4 w-4 text-indigo-400 shrink-0" />
              <span className="text-xs font-semibold text-zinc-300 truncate" title={username}>
                {username}
              </span>
            </div>
            <button
              onClick={logout}
              className="text-zinc-500 hover:text-red-400 transition-colors p-1 rounded hover:bg-zinc-800/80 cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
        <div className="text-center">
          <div className="text-xs font-semibold text-zinc-500 uppercase tracking-widest">
            SaaS Platform v1.0
          </div>
          <div className="text-[10px] text-zinc-600 mt-1">
            Serving Market Opportunities
          </div>
        </div>
      </div>
    </aside>
  );
}
