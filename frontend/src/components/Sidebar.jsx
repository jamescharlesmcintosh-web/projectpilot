import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, FolderGit2, FileText, Network, ListChecks, MonitorPlay,
  ShieldCheck, GitBranch, DollarSign, ScrollText, Settings as SettingsIcon,
  Compass, Menu, X,
} from "lucide-react";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/projects", label: "Projects", icon: FolderGit2 },
  { section: "Current Project" },
  { to: "/overview", label: "Overview", icon: Compass },
  { to: "/master-plan", label: "Master Plan", icon: FileText },
  { to: "/delegation", label: "Delegation Plan", icon: Network },
  { to: "/tasks", label: "Task Queue", icon: ListChecks },
  { to: "/preview", label: "Live Preview", icon: MonitorPlay },
  { to: "/verification", label: "Verification", icon: ShieldCheck },
  { to: "/git", label: "Git & Diffs", icon: GitBranch },
  { section: "Insights" },
  { to: "/usage", label: "Usage & Cost", icon: DollarSign },
  { to: "/activity", label: "Activity Logs", icon: ScrollText },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

function NavItems({ onNavigate }) {
  return (
    <nav className="flex flex-col gap-0.5 px-2">
      {NAV.map((item, i) => {
        if (item.section) {
          return (
            <div key={`s-${i}`} className="px-3 pb-1 pt-4 text-[10px] font-semibold uppercase tracking-wider text-[#475569]">
              {item.section}
            </div>
          );
        }
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            data-testid={`nav-${item.label.toLowerCase().replace(/[^a-z]+/g, "-")}`}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-[#0EA5E9]/10 text-[#38BDF8] border border-[#38BDF8]/30"
                  : "border border-transparent text-[#94A3B8] hover:bg-[#1C2028] hover:text-[#E2E8F0]"
              }`
            }
          >
            <Icon size={17} className="shrink-0" />
            <span className="truncate">{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      {/* Mobile toggle */}
      <button
        aria-label="Toggle navigation"
        data-testid="sidebar-mobile-toggle"
        onClick={() => setOpen((v) => !v)}
        className="fixed left-3 top-3 z-50 flex h-9 w-9 items-center justify-center rounded-md border border-[#282E3A] bg-[#14171D] text-[#94A3B8] lg:hidden"
      >
        {open ? <X size={18} /> : <Menu size={18} />}
      </button>

      {open && <div className="fixed inset-0 z-30 bg-black/60 lg:hidden" onClick={() => setOpen(false)} />}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-[#242A36] bg-[#111318] transition-transform duration-200 lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center gap-2.5 border-b border-[#242A36] px-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-[#38BDF8] to-[#0EA5E9] text-[#0D0F12]">
            <Compass size={18} strokeWidth={2.5} />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-[#E2E8F0]">ProjectPilot</div>
            <div className="font-mono text-[10px] text-[#475569]">orchestration workspace</div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto pb-6 pt-1 pp-scroll-thin">
          <NavItems onNavigate={() => setOpen(false)} />
        </div>
        <div className="border-t border-[#242A36] px-4 py-3">
          <div className="rounded-md border border-[#282E3A] bg-[#14171D] px-3 py-2">
            <div className="font-mono text-[10px] uppercase tracking-wide text-[#475569]">providers</div>
            <div className="mt-1 flex items-center gap-1.5 text-xs text-[#94A3B8]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#FBBF24]" />
              Local workspace · controlled spend
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
