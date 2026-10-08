import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, CheckCircle2, XCircle, ChevronRight } from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { PageHeader, Panel, Stat, EmptyState } from "../components/Primitives";
import { StatusBadge, fmtDate } from "../lib/ui";
import NoProject from "../components/NoProject";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "../components/ui/accordion";

export default function Verification() {
  const { current } = useProjects();
  const [runs, setRuns] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!current) return;
    setLoading(true);
    const [v, t] = await Promise.all([api.projectVerifications(current.id), api.listTasks(current.id)]);
    setRuns(v);
    setTasks(t);
    setLoading(false);
  }, [current]);

  useEffect(() => { load(); }, [load]);

  if (!current) return <NoProject />;

  const taskTitle = (id) => tasks.find((t) => t.id === id)?.title || "task";
  const taskNum = (id) => tasks.find((t) => t.id === id)?.number;
  const passed = runs.filter((r) => r.status === "passed").length;
  const failed = runs.filter((r) => r.status === "failed").length;

  return (
    <div className="space-y-6">
      <PageHeader testId="verification-header" title="Verification Results" description="Every lint / type-check / build run across this project." />

      <div className="grid grid-cols-3 gap-3">
        <Stat testId="verify-total" label="Total Runs" value={runs.length} icon={ShieldCheck} />
        <Stat testId="verify-passed" label="Passed" value={passed} accent="#4ADE80" icon={CheckCircle2} />
        <Stat testId="verify-failed" label="Failed" value={failed} accent="#F87171" icon={XCircle} />
      </div>

      {loading ? (
        <div className="text-sm text-[#64748B]">Loading…</div>
      ) : runs.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="No verification runs" description="Run verification on a task to see lint, type-check, and build results here." />
      ) : (
        <Panel testId="verify-list-panel" noPad>
          <Accordion type="multiple" className="divide-y divide-[#1E232D]">
            {runs.map((r) => (
              <AccordionItem key={r.id} value={r.id} className="border-0 px-4" data-testid={`verify-run-${r.id}`}>
                <AccordionTrigger className="py-3 hover:no-underline">
                  <div className="flex flex-1 items-center justify-between gap-3 pr-3">
                    <div className="flex min-w-0 items-center gap-3">
                      {r.status === "passed" ? <CheckCircle2 size={16} className="shrink-0 text-[#4ADE80]" /> : <XCircle size={16} className="shrink-0 text-[#F87171]" />}
                      <span className="font-mono text-xs text-[#64748B]">#{taskNum(r.task_id)}</span>
                      <span className="truncate text-sm text-[#E2E8F0]">{taskTitle(r.task_id)}</span>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <span className="font-mono text-xs text-[#64748B]">{r.checks.filter(c => c.status === "passed").length}/{r.checks.length} checks</span>
                      <StatusBadge status={r.status} />
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-4">
                  <div className="space-y-2">
                    {r.checks.map((c, i) => {
                      const ok = c.status === "passed";
                      return (
                        <div key={i} className="overflow-hidden rounded-md border border-[#282E3A] bg-[#0D0F12]">
                          <div className="flex items-center justify-between border-b border-[#282E3A] px-3 py-2">
                            <span className="flex items-center gap-2 font-mono text-xs text-[#E2E8F0]">{ok ? <CheckCircle2 size={13} className="text-[#4ADE80]" /> : <XCircle size={13} className="text-[#F87171]" />}{c.command}</span>
                            <span className={`font-mono text-xs ${ok ? "text-[#4ADE80]" : "text-[#F87171]"}`}>{c.duration_ms}ms</span>
                          </div>
                          <pre className={`overflow-x-auto whitespace-pre-wrap px-3 py-2 font-mono text-xs ${ok ? "text-[#64748B]" : "text-[#F87171]"}`}>{c.output}</pre>
                        </div>
                      );
                    })}
                    <div className="flex items-center justify-between pt-1">
                      <span className="font-mono text-[10px] text-[#475569]">{fmtDate(r.created_at)}</span>
                      <Link to={`/tasks/${r.task_id}`} className="flex items-center gap-1 text-xs text-[#38BDF8] hover:underline">Open task <ChevronRight size={12} /></Link>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </Panel>
      )}
    </div>
  );
}
