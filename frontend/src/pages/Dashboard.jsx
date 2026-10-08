import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import {
  FolderGit2, ListChecks, DollarSign, Clock3, GitBranch, MonitorPlay,
  AlertTriangle, Sparkles, Plus, FileText, Network, CheckCircle2, Activity as ActivityIcon,
} from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { PageHeader, Panel, Stat, EmptyState } from "../components/Primitives";
import { StatusBadge, TierBadge, fmtRelative, fmtDate } from "../lib/ui";
import { TIER_INFO } from "../lib/ui";
import { Button } from "../components/ui/button";

const KIND_COLOR = {
  merge: "#A78BFA", verify: "#4ADE80", edit: "#38BDF8", plan: "#38BDF8",
  approve: "#4ADE80", reject: "#F87171", error: "#F87171", preview: "#2DD4BF", info: "#64748B",
};

function QuickAction({ icon: Icon, label, onClick, to, testId }) {
  const inner = (
    <button
      data-testid={testId}
      onClick={onClick}
      className="group flex w-full items-center gap-3 rounded-md border border-[#282E3A] bg-[#14171D] px-3 py-2.5 text-left text-sm text-[#94A3B8] transition-colors hover:border-[#38BDF8]/40 hover:text-[#E2E8F0]"
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-[#1C2028] text-[#38BDF8]">
        <Icon size={16} />
      </span>
      <span className="font-medium">{label}</span>
    </button>
  );
  return to ? <Link to={to}>{inner}</Link> : inner;
}

export default function Dashboard() {
  const { current, loading: projLoading, refresh } = useProjects();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    try {
      const d = await api.dashboard(current?.id);
      setData(d);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!projLoading) load();
    // eslint-disable-next-line
  }, [current?.id, projLoading]);

  const approve = async (taskId) => {
    navigate(`/tasks/${taskId}`); return;
    toast.success("Task approved & merged to main");
    await Promise.all([load(), refresh()]);
  };

  if (loading || !data) {
    return <div className="animate-pulse text-sm text-[#64748B]">Loading dashboard…</div>;
  }

  const cp = data.current_project;
  const statusOrder = ["queued", "running", "pending_approval", "merged", "failed", "rejected"];
  const tierOrder = ["local", "cheap", "expensive", "human_review"];

  return (
    <div className="space-y-6">
      <PageHeader
        testId="dashboard-header"
        title="Dashboard"
        description={cp ? `Orchestration overview for ${cp.name}` : "Create your first project to begin."}
        actions={
          <>
            <Link to="/projects">
              <Button data-testid="qa-create-project" className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">
                <Plus size={15} /> Create Project
              </Button>
            </Link>
          </>
        }
      />

      {/* Top stat row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Stat testId="stat-active-projects" label="Active Projects" value={data.active_projects.length} icon={FolderGit2} />
        <Stat testId="stat-total-tasks" label="Tasks" value={data.total_tasks} icon={ListChecks} sub={`${data.pending_approvals.length} pending`} />
        <Stat testId="stat-pending" label="Pending Approvals" value={data.pending_approvals.length} accent="#FBBF24" icon={Clock3} />
        <Stat testId="stat-failures" label="Verify Failures" value={data.verification_failures.length} accent="#F87171" icon={AlertTriangle} />
        <Stat testId="stat-actual-cost" label="Known API Cost" value={`$${data.actual_cost.toFixed(3)}`} accent="#A78BFA" icon={DollarSign} sub="This project · current month" />
        <Stat testId="stat-previews" label="Preview Sessions" value={data.preview_sessions.length} accent="#2DD4BF" icon={MonitorPlay} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Current project + current task */}
          <Panel testId="current-project-panel" title="Current Project" subtitle="The workspace focus"
            right={cp && <StatusBadge status={cp.orchestration_status} />}>
            {cp ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                  <span className="text-base font-semibold text-[#E2E8F0]">{cp.name}</span>
                  <span className="flex items-center gap-1.5 font-mono text-xs text-[#94A3B8]">
                    <GitBranch size={13} className="text-[#38BDF8]" /> {cp.current_branch}
                  </span>
                </div>
                <p className="text-sm text-[#94A3B8] line-clamp-2">{cp.description || cp.brief || "No description."}</p>
                <div className="rounded-md border border-[#282E3A] bg-[#0D0F12] p-3">
                  <div className="mb-2 text-xs font-medium uppercase tracking-wide text-[#64748B]">Current / In-Flight Task</div>
                  {data.current_task ? (
                    <Link to={`/tasks/${data.current_task.id}`} className="flex items-center justify-between rounded-md px-1 py-1 hover:bg-[#1C2028]" data-testid="dashboard-current-task">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-[#64748B]">#{data.current_task.number}</span>
                        <span className="text-sm text-[#E2E8F0]">{data.current_task.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <TierBadge tier={data.current_task.tier} />
                        <StatusBadge status={data.current_task.status} />
                      </div>
                    </Link>
                  ) : (
                    <div className="text-sm text-[#64748B]">No task currently running.</div>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Link to="/overview"><Button variant="outline" size="sm" className="border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">Overview</Button></Link>
                  <Link to="/master-plan"><Button variant="outline" size="sm" className="border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">Master Plan</Button></Link>
                  <Link to="/tasks"><Button variant="outline" size="sm" className="border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">Task Queue</Button></Link>
                </div>
              </div>
            ) : (
              <EmptyState icon={FolderGit2} title="No project yet" description="Create a project to start orchestrating." />
            )}
          </Panel>

          {/* Pending approvals */}
          <Panel testId="pending-approvals-panel" title="Pending Approvals" subtitle="Human gate — nothing merges without you"
            right={<span className="font-mono text-xs text-[#FBBF24]">{data.pending_approvals.length}</span>}>
            {data.pending_approvals.length === 0 ? (
              <div className="py-2 text-sm text-[#64748B]">No changes awaiting approval.</div>
            ) : (
              <div className="space-y-2">
                {data.pending_approvals.map((t) => (
                  <div key={t.id} data-testid={`approval-row-${t.id}`} className="flex items-center justify-between gap-3 rounded-md border border-[#282E3A] bg-[#0D0F12] px-3 py-2">
                    <Link to={`/tasks/${t.id}`} className="flex min-w-0 items-center gap-2">
                      <span className="font-mono text-xs text-[#64748B]">#{t.number}</span>
                      <span className="truncate text-sm text-[#E2E8F0]">{t.title}</span>
                      <span className="hidden font-mono text-xs text-[#94A3B8] sm:inline">{t.branch}</span>
                    </Link>
                    <div className="flex shrink-0 items-center gap-2">
                      <TierBadge tier={t.tier} />
                      <Button size="sm" data-testid={`dashboard-approve-${t.id}`} onClick={() => approve(t.id)}
                        className="h-7 gap-1 bg-emerald-500/90 text-[#0D0F12] hover:bg-emerald-400">
                        <CheckCircle2 size={13} /> Approve
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          {/* Recent model runs */}
          <Panel testId="recent-runs-panel" title="Recent Model Runs" subtitle="Mocked provider executions">
            {data.recent_runs.length === 0 ? (
              <div className="py-2 text-sm text-[#64748B]">No model runs yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#282E3A] text-left text-xs text-[#64748B]">
                      <th className="pb-2 font-medium">Task</th>
                      <th className="pb-2 font-medium">Tier</th>
                      <th className="pb-2 font-medium">Model</th>
                      <th className="pb-2 text-right font-medium">Tokens</th>
                      <th className="pb-2 text-right font-medium">Cost</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-xs">
                    {data.recent_runs.map((r) => (
                      <tr key={r.id} className="border-b border-[#1E232D]">
                        <td className="py-2 pr-2 font-sans text-[#E2E8F0]">{r.task_title}</td>
                        <td className="py-2 pr-2"><TierBadge tier={r.tier} showIcon={false} /></td>
                        <td className="py-2 pr-2 text-[#94A3B8]">{r.model_name}</td>
                        <td className="py-2 text-right text-[#94A3B8]">{(r.tokens_in + r.tokens_out).toLocaleString()}</td>
                        <td className="py-2 text-right text-[#A78BFA]">${(r.cost || 0).toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>

        {/* Right rail */}
        <div className="space-y-6">
          {/* Quick actions */}
          <Panel testId="quick-actions-panel" title="Quick Actions">
            <div className="space-y-2">
              <QuickAction testId="qa-generate-master" icon={FileText} label="Generate Master Plan" to="/master-plan" />
              <QuickAction testId="qa-generate-delegation" icon={Network} label="Generate Delegation Plan" to="/delegation" />
              <QuickAction testId="qa-create-task" icon={ListChecks} label="Create Task" to="/tasks" />
              <QuickAction testId="qa-open-preview" icon={MonitorPlay} label="Open Live Preview" to="/preview" />
              <QuickAction testId="qa-review-approvals" icon={CheckCircle2} label="Review Approvals" to="/git" />
            </div>
          </Panel>

          {/* Tasks by status */}
          <Panel testId="tasks-by-status-panel" title="Tasks by Status">
            <div className="space-y-2">
              {statusOrder.filter((s) => data.tasks_by_status[s]).map((s) => (
                <div key={s} className="flex items-center justify-between">
                  <StatusBadge status={s} />
                  <span className="font-mono text-sm text-[#E2E8F0]">{data.tasks_by_status[s]}</span>
                </div>
              ))}
              {Object.keys(data.tasks_by_status).length === 0 && <div className="text-sm text-[#64748B]">No tasks yet.</div>}
            </div>
          </Panel>

          {/* Tasks by tier */}
          <Panel testId="tasks-by-tier-panel" title="Tasks by Model Tier" subtitle="Minimize expensive usage">
            <div className="space-y-2">
              {tierOrder.filter((t) => data.tasks_by_tier[t]).map((t) => (
                <div key={t} className="flex items-center justify-between">
                  <TierBadge tier={t} />
                  <span className="font-mono text-sm text-[#E2E8F0]">{data.tasks_by_tier[t]}</span>
                </div>
              ))}
              {Object.keys(data.tasks_by_tier).length === 0 && <div className="text-sm text-[#64748B]">No tasks yet.</div>}
            </div>
          </Panel>

          {/* Verification failures */}
          {data.verification_failures.length > 0 && (
            <Panel testId="verify-failures-panel" title="Verification Failures">
              <div className="space-y-2">
                {data.verification_failures.slice(0, 4).map((v) => (
                  <div key={v.id} className="rounded-md border border-rose-900/50 bg-rose-950/20 px-3 py-2 text-xs">
                    <div className="flex items-center gap-1.5 text-rose-300"><AlertTriangle size={12} /> {v.checks.filter(c => c.status === "failed").map(c => c.name).join(", ")} failed</div>
                    <div className="mt-0.5 font-mono text-[#64748B]">{fmtRelative(v.created_at)}</div>
                  </div>
                ))}
              </div>
            </Panel>
          )}

          {/* Recent activity */}
          <Panel testId="recent-activity-panel" title="Recent Activity" right={<ActivityIcon size={14} className="text-[#64748B]" />}>
            <div className="space-y-3">
              {data.recent_activity.length === 0 && <div className="text-sm text-[#64748B]">No activity yet.</div>}
              {data.recent_activity.map((a) => (
                <div key={a.id} className="flex gap-2.5">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: KIND_COLOR[a.kind] || "#64748B" }} />
                  <div className="min-w-0">
                    <div className="text-xs text-[#94A3B8]">{a.message}</div>
                    <div className="font-mono text-[10px] text-[#475569]">{fmtDate(a.created_at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
