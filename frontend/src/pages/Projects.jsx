import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Plus, FolderGit2, GitBranch, Sparkles, Trash2, Cpu } from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { SAMPLE_BRIEF } from "../lib/sample";
import { PageHeader, Panel, EmptyState, Field } from "../components/Primitives";
import { StatusBadge, fmtRelative } from "../lib/ui";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";

const emptyForm = {
  name: "", description: "", brief: "", repo_url: "", local_path: "",
  tech_stack: "HTML, CSS, JavaScript", project_type: "website", deployment_target: "", primary_developer: "You", status: "active",
};

export default function Projects() {
  const { projects, setCurrentId, refresh, currentId } = useProjects();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e?.target ? e.target.value : e }));

  const loadSample = () => setForm({ ...SAMPLE_BRIEF });

  const submit = async () => {
    if (!form.name.trim()) return toast.error("Project name is required");
    setSaving(true);
    try {
      const p = await api.createProject(form);
      await refresh();
      setCurrentId(p.id);
      toast.success(`Project "${p.name}" created`);
      setOpen(false);
      setForm(emptyForm);
      navigate("/overview");
    } catch (e) {
      toast.error("Failed to create project");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id, name) => {
    if (!window.confirm(`Archive project "${name}"? Source and history will be retained.`)) return;
    await api.deleteProject(id);
    toast.success("Project archived");
    await refresh();
  };

  return (
    <div className="space-y-6">
      <PageHeader
        testId="projects-header"
        title="Projects"
        description="Every project is Git-oriented and orchestrated through the plan → delegate → verify → approve workflow."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button data-testid="new-project-btn" className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">
                <Plus size={15} /> New Project
              </Button>
            </DialogTrigger>
            <DialogContent className="max-h-[90vh] overflow-y-auto border-[#282E3A] bg-[#14171D] text-[#E2E8F0] sm:max-w-2xl">
              <DialogHeader>
                <DialogTitle className="flex items-center justify-between">
                  <span>Create Project</span>
                  <Button variant="outline" size="sm" data-testid="load-sample-btn" onClick={loadSample}
                    className="gap-1.5 border-[#A78BFA]/40 bg-transparent text-[#A78BFA] hover:bg-[#A78BFA]/10">
                    <Sparkles size={13} /> Load Sample Brief
                  </Button>
                </DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-1 gap-4 py-2 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Field label="Project name">
                    <Input data-testid="form-name" value={form.name} onChange={set("name")} placeholder="e.g. Contractor Storage Yard Website" className="border-[#282E3A] bg-[#0D0F12]" />
                  </Field>
                </div>
                <div className="sm:col-span-2">
                  <Field label="Short description">
                    <Input data-testid="form-description" value={form.description} onChange={set("description")} placeholder="One-line summary" className="border-[#282E3A] bg-[#0D0F12]" />
                  </Field>
                </div>
                <div className="sm:col-span-2">
                  <Field label="Project brief" hint="The detailed brief the master plan is generated from.">
                    <Textarea data-testid="form-brief" value={form.brief} onChange={set("brief")} rows={5} placeholder="Describe goals, audience, must-haves, and constraints…" className="border-[#282E3A] bg-[#0D0F12] font-mono text-xs" />
                  </Field>
                </div>
                <Field label="Repository URL (reference only)"><Input data-testid="form-repo" value={form.repo_url} onChange={set("repo_url")} placeholder="git@github.com:org/repo.git" className="border-[#282E3A] bg-[#0D0F12] font-mono text-xs" /></Field>
                <Field label="Local path (reference only)"><Input data-testid="form-local-path" value={form.local_path} onChange={set("local_path")} placeholder="~/dev/repo" className="border-[#282E3A] bg-[#0D0F12] font-mono text-xs" /></Field>
                <Field label="Technology stack"><Input data-testid="form-stack" value={form.tech_stack} onChange={set("tech_stack")} placeholder="React, TypeScript, Tailwind…" className="border-[#282E3A] bg-[#0D0F12]" /></Field>
                <Field label="Project type">
                  <Select value={form.project_type} onValueChange={set("project_type")}>
                    <SelectTrigger data-testid="form-type" className="border-[#282E3A] bg-[#0D0F12]"><SelectValue /></SelectTrigger>
                    <SelectContent className="border-[#282E3A] bg-[#1C2028] text-[#E2E8F0]">
                      {["website", "marketing_site", "web_app", "mobile_app", "portfolio", "e-commerce", "api_service"].map((t) => (
                        <SelectItem key={t} value={t} className="focus:bg-[#282E3A]">{t}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
                <Field label="Deployment target"><Input data-testid="form-deploy" value={form.deployment_target} onChange={set("deployment_target")} placeholder="Static host / edge CDN" className="border-[#282E3A] bg-[#0D0F12]" /></Field>
                <Field label="Primary developer"><Input data-testid="form-dev" value={form.primary_developer} onChange={set("primary_developer")} placeholder="You" className="border-[#282E3A] bg-[#0D0F12]" /></Field>
                <Field label="Project status">
                  <Select value={form.status} onValueChange={set("status")}>
                    <SelectTrigger data-testid="form-status" className="border-[#282E3A] bg-[#0D0F12]"><SelectValue /></SelectTrigger>
                    <SelectContent className="border-[#282E3A] bg-[#1C2028] text-[#E2E8F0]">
                      {["active", "paused", "archived", "completed"].map((t) => (
                        <SelectItem key={t} value={t} className="focus:bg-[#282E3A]">{t}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </Field>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setOpen(false)} className="border-[#282E3A] bg-transparent text-[#94A3B8]">Cancel</Button>
                <Button data-testid="submit-project-btn" onClick={submit} disabled={saving} className="bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">
                  {saving ? "Creating…" : "Create Project"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      {projects.length === 0 ? (
        <EmptyState icon={FolderGit2} title="No projects yet" description="Create your first project or load the sample brief to explore the full workflow." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((p) => (
            <div
              key={p.id}
              data-testid={`project-card-${p.id}`}
              className={`group cursor-pointer rounded-lg border bg-[#14171D] p-4 transition-colors ${
                currentId === p.id ? "border-[#38BDF8]/50" : "border-[#282E3A] hover:border-[#3A424F]"
              }`}
              onClick={() => { setCurrentId(p.id); navigate("/overview"); }}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#1C2028] text-[#38BDF8]"><FolderGit2 size={17} /></span>
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-[#E2E8F0]">{p.name}</div>
                    <div className="font-mono text-[10px] text-[#475569]">{p.project_type}</div>
                  </div>
                </div>
                <StatusBadge status={p.status} />
              </div>
              <p className="mt-3 line-clamp-2 text-xs text-[#94A3B8]">{p.description || p.brief || "No description."}</p>
              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[10px] text-[#64748B]">
                <span className="flex items-center gap-1"><GitBranch size={11} className="text-[#38BDF8]" /> {p.current_branch}</span>
                <span className="flex items-center gap-1"><Cpu size={11} /> {p.has_master_plan ? "planned" : "no plan"}</span>
                <span>updated {fmtRelative(p.updated_at)}</span>
              </div>
              <div className="mt-3 flex items-center justify-between border-t border-[#1E232D] pt-3">
                <span className="text-xs text-[#64748B]">{currentId === p.id ? "Current workspace" : "Click to open"}</span>
                <button
                  aria-label={`Archive ${p.name}`}
                  data-testid={`delete-project-${p.id}`}
                  onClick={(e) => { e.stopPropagation(); remove(p.id, p.name); }}
                  className="rounded p-1 text-[#64748B] transition-opacity hover:text-rose-400"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
