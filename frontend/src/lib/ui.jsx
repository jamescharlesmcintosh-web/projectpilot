import React from "react";
import { Cpu, Zap, Sparkles, UserCheck } from "lucide-react";

export const TIER_INFO = {
  auto: { label: "Auto", icon: Cpu, badge: "bg-sky-950/60 text-sky-300 border-sky-800/60", dot: "#38BDF8" },
  local: { label: "Local", icon: Cpu, badge: "bg-teal-950/60 text-teal-300 border-teal-800/60", dot: "#2DD4BF" },
  cheap: { label: "Standard", icon: Zap, badge: "bg-sky-950/60 text-sky-300 border-sky-800/60", dot: "#38BDF8" },
  expensive: { label: "Advanced", icon: Sparkles, badge: "bg-purple-950/60 text-purple-300 border-purple-800/60", dot: "#A78BFA" },
  human_review: { label: "Human Review", icon: UserCheck, badge: "bg-amber-950/60 text-amber-300 border-amber-800/60", dot: "#FBBF24" },
};

export const STATUS_INFO = {
  ready: { label: "Ready to check", badge: "bg-sky-950 text-sky-300 border-sky-800" },
  superseded: { label: "Older plan", badge: "bg-slate-800 text-slate-400 border-slate-700" },
  queued: { label: "Queued", badge: "bg-slate-800/80 text-slate-300 border-slate-600/60" },
  running: { label: "Running", badge: "bg-sky-950/80 text-sky-300 border-sky-700/70" },
  pending_approval: { label: "Pending Approval", badge: "bg-amber-950/80 text-amber-300 border-amber-700/70" },
  approved: { label: "Approved", badge: "bg-blue-950/80 text-blue-300 border-blue-700/70" },
  merged: { label: "Merged", badge: "bg-purple-950/80 text-purple-300 border-purple-700/70" },
  rejected: { label: "Rejected", badge: "bg-rose-950/80 text-rose-300 border-rose-700/70" },
  failed: { label: "Failed", badge: "bg-rose-950/80 text-rose-300 border-rose-700/70" },
  passed: { label: "Passed", badge: "bg-emerald-950/80 text-emerald-300 border-emerald-700/70" },
  idle: { label: "Idle", badge: "bg-slate-800/80 text-slate-400 border-slate-600/60" },
  planning: { label: "Planning", badge: "bg-sky-950/80 text-sky-300 border-sky-700/70" },
  executing: { label: "Executing", badge: "bg-sky-950/80 text-sky-300 border-sky-700/70" },
  awaiting_approval: { label: "Awaiting Approval", badge: "bg-amber-950/80 text-amber-300 border-amber-700/70" },
  active: { label: "Active", badge: "bg-emerald-950/80 text-emerald-300 border-emerald-700/70" },
  paused: { label: "Paused", badge: "bg-slate-800/80 text-slate-400 border-slate-600/60" },
  archived: { label: "Archived", badge: "bg-slate-800/80 text-slate-500 border-slate-700/60" },
  completed: { label: "Completed", badge: "bg-purple-950/80 text-purple-300 border-purple-700/70" },
  success: { label: "Success", badge: "bg-emerald-950/80 text-emerald-300 border-emerald-700/70" },
  stopped: { label: "Stopped", badge: "bg-slate-800/80 text-slate-400 border-slate-600/60" },
};

export function StatusBadge({ status, testId }) {
  const info = STATUS_INFO[status] || { label: status, badge: "bg-slate-800/80 text-slate-300 border-slate-600/60" };
  const pulse = status === "running" || status === "executing";
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${info.badge}`}
    >
      {pulse && <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />}
      {info.label}
    </span>
  );
}

export function TierBadge({ tier, testId, showIcon = true }) {
  const info = TIER_INFO[tier] || TIER_INFO.cheap;
  const Icon = info.icon;
  return (
    <span
      data-testid={testId}
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${info.badge}`}
    >
      {showIcon && <Icon size={12} />}
      {info.label}
    </span>
  );
}

export function fmtDate(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

export function fmtRelative(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  const s = Math.floor((Date.now() - d.getTime()) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}
