import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  GitBranch, FolderGit2, FileText, Network, ListChecks, Server, Rocket, User, Layers, Target,
} from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { PageHeader, Panel } from "../components/Primitives";
import { StatusBadge } from "../lib/ui";
import { Button } from "../components/ui/button";
import ProjectFiles from '../components/ProjectFiles';
import NoProject from "../components/NoProject";

function Meta({ icon: Icon, label, value, mono }) {
  return (
    <div className="flex items-start gap-3 rounded-md border border-[#282E3A] bg-[#0D0F12] px-3 py-2.5">
      <Icon size={15} className="mt-0.5 shrink-0 text-[#64748B]" />
      <div className="min-w-0">
        <div className="text-[10px] font-medium uppercase tracking-wide text-[#64748B]">{label}</div>
        <div className={`truncate text-sm text-[#E2E8F0] ${mono ? "font-mono text-xs" : ""}`}>{value || "—"}</div>
      </div>
    </div>
  );
}

const STEPS = [
  { key: "brief", label: "Project Brief" },
  { key: "master", label: "Master Plan" },
  { key: "delegation", label: "Delegation Plan" },
  { key: "tasks", label: "Task Queue" },
  { key: "verify", label: "Verification" },
  { key: "approval", label: "Human Approval" },
];

export default function ProjectOverview() {
  const { current } = useProjects();
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    if (current) api.listTasks(current.id).then(setTasks);
  }, [current]);

  if (!current) return <NoProject />;

  const progress = {
    brief: !!current.brief,
    master: !!current.approved_plan_id,
    delegation: current.has_delegation_plan,
    tasks: tasks.length > 0,
    verify: tasks.some((t) => ["pending_approval", "merged"].includes(t.status)),
    approval: tasks.some((t) => t.status === "merged"),
  };

  return (
    <div className="space-y-6">
      <PageHeader
        testId="overview-header"
        title={current.name}
        description={current.description}
        actions={<StatusBadge status={current.orchestration_status} />}
      />

      <ProjectFiles/>
      {/* Workflow progress */}
      <Panel testId="workflow-progress-panel" title="Orchestration Workflow" subtitle="Nothing merges or deploys without explicit human approval">
        <div className="flex flex-wrap items-center gap-2">
          {STEPS.map((s, i) => {
            const done = progress[s.key];
            return (
              <React.Fragment key={s.key}>
                <div
                  data-testid={`workflow-step-${s.key}`}
                  className={`flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium ${
                    done ? "border-emerald-700/60 bg-emerald-950/40 text-emerald-300" : "border-[#282E3A] bg-[#0D0F12] text-[#64748B]"
                  }`}
                >
                  <span className={`flex h-4 w-4 items-center justify-center rounded-full text-[10px] ${done ? "bg-emerald-500 text-[#0D0F12]" : "bg-[#282E3A] text-[#64748B]"}`}>
                    {done ? "✓" : i + 1}
                  </span>
                  {s.label}
                </div>
                {i < STEPS.length - 1 && <span className="text-[#3A424F]">→</span>}
              </React.Fragment>
            );
          })}
        </div>
      </Panel>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Panel testId="brief-panel" title="Project Brief">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-[#94A3B8]">{current.brief || "No brief provided."}</p>
          </Panel>

          <Panel testId="quick-links-panel" title="Continue the workflow">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <Link to="/master-plan"><Button variant="outline" className="w-full justify-start gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]"><FileText size={15} /> Master Plan</Button></Link>
              <Link to="/delegation"><Button variant="outline" className="w-full justify-start gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]"><Network size={15} /> Delegation</Button></Link>
              <Link to="/tasks"><Button variant="outline" className="w-full justify-start gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]"><ListChecks size={15} /> Tasks</Button></Link>
            </div>
          </Panel>
        </div>

        <div className="space-y-3">
          <Meta icon={FolderGit2} label="Repository" value={current.repo_url} mono />
          <Meta icon={Server} label="Local path" value={current.local_path} mono />
          <Meta icon={GitBranch} label="Current branch" value={current.current_branch} mono />
          <Meta icon={Layers} label="Tech stack" value={current.tech_stack} />
          <Meta icon={Target} label="Project type" value={current.project_type} mono />
          <Meta icon={Rocket} label="Deployment target" value={current.deployment_target} />
          <Meta icon={User} label="Primary developer" value={current.primary_developer} />
        </div>
      </div>
    </div>
  );
}
