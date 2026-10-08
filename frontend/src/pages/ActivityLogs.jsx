import React, { useEffect, useState, useCallback } from "react";
import {
  ScrollText, GitMerge, ShieldCheck, Wand2, FileText, MonitorPlay, XCircle, Info, AlertTriangle,
} from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { PageHeader, Panel, EmptyState } from "../components/Primitives";
import { fmtDate } from "../lib/ui";
import NoProject from "../components/NoProject";

const KIND = {
  merge: { icon: GitMerge, color: "#A78BFA", label: "Merge" },
  verify: { icon: ShieldCheck, color: "#4ADE80", label: "Verify" },
  edit: { icon: Wand2, color: "#38BDF8", label: "Edit" },
  plan: { icon: FileText, color: "#38BDF8", label: "Plan" },
  preview: { icon: MonitorPlay, color: "#2DD4BF", label: "Preview" },
  reject: { icon: XCircle, color: "#F87171", label: "Reject" },
  error: { icon: AlertTriangle, color: "#F87171", label: "Error" },
  approve: { icon: ShieldCheck, color: "#4ADE80", label: "Approve" },
  info: { icon: Info, color: "#64748B", label: "Info" },
};

export default function ActivityLogs() {
  const { current } = useProjects();
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!current) return;
    setLoading(true);
    setLogs(await api.activity(current.id));
    setLoading(false);
  }, [current]);

  useEffect(() => { load(); }, [load]);

  if (!current) return <NoProject />;

  const kinds = ["all", ...Array.from(new Set(logs.map((l) => l.kind)))];
  const shown = logs.filter((l) => filter === "all" || l.kind === filter);

  return (
    <div className="space-y-6">
      <PageHeader testId="activity-header" title="Project State & Activity" description={`Full event log for ${current.name}.`} />

      <div className="flex flex-wrap gap-1.5">
        {kinds.map((k) => (
          <button key={k} data-testid={`activity-filter-${k}`} onClick={() => setFilter(k)}
            className={`rounded-md border px-2.5 py-1 text-xs font-medium capitalize transition-colors ${filter === k ? "border-[#38BDF8]/50 bg-[#38BDF8]/10 text-[#38BDF8]" : "border-[#282E3A] bg-[#14171D] text-[#64748B] hover:text-[#94A3B8]"}`}>
            {k === "all" ? "All" : (KIND[k]?.label || k)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-sm text-[#64748B]">Loading…</div>
      ) : shown.length === 0 ? (
        <EmptyState icon={ScrollText} title="No activity" description="Actions like generating plans, running edits, verifying, and merging appear here." />
      ) : (
        <Panel testId="activity-timeline-panel" noPad>
          <div className="p-4">
            <div className="relative space-y-1 pl-4">
              <div className="absolute bottom-2 left-[7px] top-2 w-px bg-[#282E3A]" />
              {shown.map((a) => {
                const info = KIND[a.kind] || KIND.info;
                const Icon = info.icon;
                return (
                  <div key={a.id} data-testid={`activity-item-${a.id}`} className="relative flex gap-3 py-2">
                    <span className="relative z-10 mt-0.5 flex h-4 w-4 items-center justify-center rounded-full ring-4 ring-[#14171D]" style={{ background: info.color }}>
                      <span className="h-1.5 w-1.5 rounded-full bg-[#0D0F12]" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Icon size={13} style={{ color: info.color }} />
                        <span className="text-sm text-[#E2E8F0]">{a.message}</span>
                      </div>
                      <span className="font-mono text-[10px] text-[#475569]">{fmtDate(a.created_at)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Panel>
      )}
    </div>
  );
}
