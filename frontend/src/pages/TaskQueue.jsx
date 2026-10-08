import React, { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ListChecks, Plus, ListPlus, Filter } from "lucide-react";
import api, { errorMessage } from "../lib/api";
import { useProjects } from "../lib/store";
import { PageHeader, Panel, EmptyState, Field } from "../components/Primitives";
import { StatusBadge, TierBadge, TIER_INFO, fmtRelative } from "../lib/ui";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import NoProject from "../components/NoProject";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";

export default function TaskQueue() {
  const { current, refreshCurrent } = useProjects();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", tier: "auto" });
  const navigate = useNavigate();

  const load = useCallback(async () => {
    if (!current) return;
    setLoading(true);
    setTasks(await api.listTasks(current.id));
    setLoading(false);
  }, [current]);

  useEffect(() => { load(); }, [load]);

  const materialize = async () => {
    try {
      const r = await api.materializeTasks(current.id);
      toast.success(r.created > 0 ? `${r.created} task(s) added from delegation plan` : "Nothing new to add");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Generate a delegation plan first");
    }
  };

  const createTask = async () => {
    if (!form.title.trim()) return toast.error("Title required");
    try { await api.createTask(current.id, {...form, acceptance_criteria: (form.criteria||"The requested behavior works in the preview.").split("\n").filter(Boolean), verification_commands:(form.commands||"").split("\n").filter(Boolean), criteria:undefined,commands:undefined}); } catch(e) { toast.error(errorMessage(e)); return; }
    toast.success("Task created");
    setOpen(false);
    setForm({ title: "", description: "", tier: "auto" });
    load();
  };

  const changeTier = async (taskId, tier) => {
    try { await api.assignTier(taskId, tier); } catch(e) { toast.error(errorMessage(e)); return; }
    toast.success(`Tier changed to ${TIER_INFO[tier].label}`);
    load();
  };

  if (!current) return <NoProject />;

  const shown = tasks.filter((t) => filter === "all" || t.status === filter);

  return (
    <div className="space-y-6">
      <PageHeader
        testId="task-queue-header"
        title="Task Queue"
        description="Build small, dependency-aware tasks. Choose a model, inspect real changes, and approve when verified."
        actions={
          <div className="flex gap-2">
            <Button data-testid="queue-materialize-btn" variant="outline" onClick={materialize}
              className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
              <ListPlus size={15} /> From Delegation Plan
            </Button>
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button data-testid="new-task-btn" className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]"><Plus size={15} /> New Task</Button>
              </DialogTrigger>
              <DialogContent className="border-[#282E3A] bg-[#14171D] text-[#E2E8F0]">
                <DialogHeader><DialogTitle>Create Task</DialogTitle></DialogHeader>
                <div className="space-y-4 py-2">
                  <Field label="Title"><Input data-testid="task-form-title" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} className="border-[#282E3A] bg-[#0D0F12]" placeholder="e.g. Build hero section" /></Field>
                  <Field label="Description"><Textarea data-testid="task-form-desc" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={3} className="border-[#282E3A] bg-[#0D0F12]" /></Field>
                  <Field label="Acceptance criteria (one per line)"><textarea className="pp-input" rows={3} value={form.criteria||""} onChange={e=>setForm(f=>({...f,criteria:e.target.value}))}/></Field><Field label="Verification commands (optional; run only in Docker)"><textarea className="pp-input font-mono text-xs" rows={2} value={form.commands||""} onChange={e=>setForm(f=>({...f,commands:e.target.value}))}/></Field><Field label="Model tier">
                    <Select value={form.tier} onValueChange={(v) => setForm((f) => ({ ...f, tier: v }))}>
                      <SelectTrigger data-testid="task-form-tier" className="border-[#282E3A] bg-[#0D0F12]"><SelectValue /></SelectTrigger>
                      <SelectContent className="border-[#282E3A] bg-[#1C2028] text-[#E2E8F0]">
                        {Object.keys(TIER_INFO).map((t) => <SelectItem key={t} value={t} className="focus:bg-[#282E3A]">{TIER_INFO[t].label}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </Field>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setOpen(false)} className="border-[#282E3A] bg-transparent text-[#94A3B8]">Cancel</Button>
                  <Button data-testid="submit-task-btn" onClick={createTask} className="bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">Create</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      <div className="flex items-center gap-2">
        <Filter size={14} className="text-[#64748B]" />
        <div className="flex flex-wrap gap-1.5">
          {["all", "queued", "ready", "superseded", "running", "pending_approval", "merged", "failed", "rejected"].map((s) => (
            <button
              key={s}
              data-testid={`filter-${s}`}
              onClick={() => setFilter(s)}
              className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                filter === s ? "border-[#38BDF8]/50 bg-[#38BDF8]/10 text-[#38BDF8]" : "border-[#282E3A] bg-[#14171D] text-[#64748B] hover:text-[#94A3B8]"
              }`}
            >
              {s === "all" ? "All" : (s.replace("_", " "))}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-[#64748B]">Loading…</div>
      ) : tasks.length === 0 ? (
        <EmptyState
          testId="no-tasks"
          icon={ListChecks}
          title="No tasks in the queue"
          description="Materialize tasks from your delegation plan, or create one manually."
          action={<Button data-testid="empty-materialize" onClick={materialize} className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]"><ListPlus size={15} /> From Delegation Plan</Button>}
        />
      ) : (
        <Panel noPad testId="task-table-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#282E3A] text-left text-xs text-[#64748B]">
                  <th className="px-4 py-3 font-medium">#</th>
                  <th className="px-4 py-3 font-medium">Task</th>
                  <th className="px-4 py-3 font-medium">Branch</th>
                  <th className="px-4 py-3 font-medium">Tier</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Updated</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {shown.map((t) => (
                  <tr key={t.id} data-testid={`task-row-${t.id}`} className="border-b border-[#1E232D] hover:bg-[#1C2028]/50">
                    <td className="px-4 py-3 font-mono text-xs text-[#64748B]">{String(t.number).padStart(2, "0")}</td>
                    <td className="px-4 py-3">
                      <Link to={`/tasks/${t.id}`} className="font-medium text-[#E2E8F0] hover:text-[#38BDF8]">{t.title}</Link>{t.dependencies.some(id=>tasks.find(d=>d.id===id)?.status!=="merged")&&<div className="mt-1 text-xs text-amber-200">Waiting on dependencies</div>}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-[#94A3B8]">{t.branch || "—"}</td>
                    <td className="px-4 py-3">
                      <Select disabled={! ["queued","failed","rejected"].includes(t.status)} value={t.tier} onValueChange={(v) => changeTier(t.id, v)}>
                        <SelectTrigger data-testid={`tier-select-${t.id}`} className="h-7 w-[140px] border-[#282E3A] bg-[#0D0F12] text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent className="border-[#282E3A] bg-[#1C2028] text-[#E2E8F0]">
                          {Object.keys(TIER_INFO).map((tt) => <SelectItem key={tt} value={tt} className="text-xs focus:bg-[#282E3A]">{TIER_INFO[tt].label}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={t.status} testId={`task-status-${t.id}`} /></td>
                    <td className="px-4 py-3 font-mono text-xs text-[#64748B]">{fmtRelative(t.updated_at)}</td>
                    <td className="px-4 py-3 text-right">
                      <Button size="sm" variant="outline" data-testid={`open-task-${t.id}`} onClick={() => navigate(`/tasks/${t.id}`)}
                        className="h-7 border-[#282E3A] bg-transparent text-xs text-[#94A3B8] hover:text-[#E2E8F0]">Open</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
