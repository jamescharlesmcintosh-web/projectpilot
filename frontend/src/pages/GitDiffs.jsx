import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { GitBranch, GitMerge, CheckCircle2, XCircle, GitCommit, ChevronRight } from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { PageHeader, Panel, EmptyState } from "../components/Primitives";
import { StatusBadge, TierBadge, fmtRelative } from "../lib/ui";
import { Button } from "../components/ui/button";
import NoProject from "../components/NoProject";
import DiffViewer from "../components/DiffViewer";

export default function GitDiffs() {
  const { current, refreshCurrent } = useProjects();
  const [tasks, setTasks] = useState([]);
  const [diffs, setDiffs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!current) return;
    setLoading(true);
    const [t, d] = await Promise.all([api.listTasks(current.id), api.projectDiffs(current.id)]);
    setTasks(t);
    setDiffs(d);
    setSelected(d[0] || null);
    setLoading(false);
  }, [current]);

  useEffect(() => { load(); }, [load]);

  if (!current) return <NoProject />;

  const taskFor = (taskId) => tasks.find((t) => t.id === taskId);
  const pending = tasks.filter((t) => t.status === "pending_approval");

  // build branch list
  const branches = [{ name: current.default_branch, kind: "trunk" }];
  tasks.filter((t) => t.branch).forEach((t) => {
    if (!branches.some((b) => b.name === t.branch)) branches.push({ name: t.branch, kind: "preview", task: t });
  });

  const approve = async (taskId) => {
    window.location.assign(`/tasks/${taskId}`); return;
    toast.success("Merged to main");
    await Promise.all([load(), refreshCurrent()]);
  };
  const reject = async (taskId) => {
    await api.reject(taskId);
    toast("Edit rejected");
    await Promise.all([load(), refreshCurrent()]);
  };

  return (
    <div className="space-y-6">
      <PageHeader testId="git-header" title="Git Branches & Diffs" description="Review proposed changes per preview branch. Merges happen only on explicit approval." />

      {pending.length > 0 && (
        <Panel testId="git-approvals-panel" title="Awaiting Approval" subtitle="Human gate before merge to main"
          right={<span className="font-mono text-xs text-[#FBBF24]">{pending.length}</span>}>
          <div className="space-y-2">
            {pending.map((t) => (
              <div key={t.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-amber-800/40 bg-amber-950/10 px-3 py-2">
                <div className="flex min-w-0 items-center gap-2">
                  <span className="font-mono text-xs text-[#64748B]">#{t.number}</span>
                  <span className="truncate text-sm text-[#E2E8F0]">{t.title}</span>
                  <span className="font-mono text-xs text-[#94A3B8]">{t.branch}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="sm" data-testid={`git-approve-${t.id}`} onClick={() => approve(t.id)} className="h-7 gap-1 bg-emerald-500/90 text-[#0D0F12] hover:bg-emerald-400"><CheckCircle2 size={13} /> Review & Approve</Button>
                  <Button size="sm" variant="outline" data-testid={`git-reject-${t.id}`} onClick={() => reject(t.id)} className="h-7 gap-1 border-rose-900/50 bg-transparent text-rose-300 hover:bg-rose-950/30"><XCircle size={13} /> Reject</Button>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <Panel testId="branches-panel" title="Branches">
            <div className="space-y-1.5">
              {branches.map((b) => (
                <div key={b.name} className="flex items-center justify-between rounded-md border border-[#282E3A] bg-[#0D0F12] px-3 py-2">
                  <span className="flex items-center gap-1.5 font-mono text-xs text-[#E2E8F0]">
                    {b.kind === "trunk" ? <GitMerge size={13} className="text-[#A78BFA]" /> : <GitBranch size={13} className="text-[#38BDF8]" />}
                    {b.name}
                  </span>
                  {b.task && <StatusBadge status={b.task.status} />}
                  {b.kind === "trunk" && <span className="rounded bg-[#1C2028] px-1.5 py-0.5 font-mono text-[10px] text-[#64748B]">trunk</span>}
                </div>
              ))}
            </div>
          </Panel>

          <Panel testId="diff-list-panel" title="Diffs">
            <div className="space-y-1.5">
              {diffs.length === 0 && <div className="text-sm text-[#64748B]">No diffs yet.</div>}
              {diffs.map((d) => {
                const t = taskFor(d.task_id);
                return (
                  <button key={d.id} data-testid={`diff-list-${d.id}`} onClick={() => setSelected(d)}
                    className={`w-full rounded-md border px-3 py-2 text-left transition-colors ${selected?.id === d.id ? "border-[#38BDF8]/50 bg-[#38BDF8]/5" : "border-[#282E3A] bg-[#0D0F12] hover:border-[#3A424F]"}`}>
                    <div className="flex items-center justify-between">
                      <span className="truncate font-mono text-xs text-[#38BDF8]">{d.branch}</span>
                      {t && <TierBadge tier={t.tier} showIcon={false} />}
                    </div>
                    <div className="mt-1 truncate text-xs text-[#94A3B8]">{t?.title || "task"}</div>
                    <div className="mt-0.5 font-mono text-[10px] text-[#475569]">{d.summary} · {fmtRelative(d.created_at)}</div>
                  </button>
                );
              })}
            </div>
          </Panel>
        </div>

        <div className="lg:col-span-2">
          <Panel testId="diff-detail-panel" title="Diff Review" subtitle={selected ? selected.branch : undefined}
            right={selected && taskFor(selected.task_id) && (
              <Link to={`/tasks/${selected.task_id}`}><Button size="sm" variant="outline" className="h-7 gap-1 border-[#282E3A] bg-transparent text-xs text-[#94A3B8] hover:text-[#E2E8F0]">Open task <ChevronRight size={12} /></Button></Link>
            )}>
            {loading ? <div className="text-sm text-[#64748B]">Loading…</div> :
              selected ? <DiffViewer diff={selected} testId="git-diff-viewer" /> :
                <EmptyState icon={GitCommit} title="No diff selected" description="Select a diff from the list to review its changes." />}
          </Panel>
        </div>
      </div>
    </div>
  );
}
