import PlanControls from "../components/PlanControls";
import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { FileText, Sparkles, RefreshCw, ChevronDown, Download, Copy, GitCompare } from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { masterPlanToMarkdown, downloadMarkdown, copyMarkdown, planFilename } from "../lib/markdown";
import { diffLines } from "../lib/diff";
import PlanDiffDialog from "../components/PlanDiffDialog";
import CostEstimate from "../components/CostEstimate";
import { PageHeader, Panel, EmptyState } from "../components/Primitives";
import { TierBadge } from "../lib/ui";
import { Button } from "../components/ui/button";
import NoProject from "../components/NoProject";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "../components/ui/accordion";

function ListSection({ title, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#64748B]">{title}</h4>
      <ul className="space-y-1.5">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2 text-sm text-[#94A3B8]">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-[#38BDF8]" />
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TextSection({ title, text }) {
  if (!text) return null;
  return (
    <div>
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#64748B]">{title}</h4>
      <pre className="whitespace-pre-wrap rounded-md border border-[#282E3A] bg-[#0D0F12] p-3 font-mono text-xs leading-relaxed text-[#94A3B8]">{text}</pre>
    </div>
  );
}

export default function MasterPlan() {
  const { current, refreshCurrent } = useProjects();
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [diffRows, setDiffRows] = useState(null);
  const [diffOpen, setDiffOpen] = useState(false);
  const [costVersion, setCostVersion] = useState(0);

  const load = useCallback(() => {
    const pid = current?.id;
    if (!pid) { setLoading(false); return () => {}; }
    let cancelled = false;
    setLoading(true);
    api.getMasterPlan(pid)
      .then((p) => { if (!cancelled) setPlan(p); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.id]);

  useEffect(() => load(), [load]);

  const generate = async () => {
    setGenerating(true);
    try {
      const prevMd = plan ? masterPlanToMarkdown(current, plan) : null;
      const p = await api.generateMasterPlan(current.id);
      setPlan(p);
      if (prevMd) {
        setDiffRows(diffLines(prevMd, masterPlanToMarkdown(current, p)));
        setDiffOpen(true);
      }
      refreshCurrent();
      toast.success(`Master plan generated — ${p.roadmap.length} roadmap tasks`);
      setCostVersion((v) => v + 1);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to generate master plan");
    } finally {
      setGenerating(false);
    }
  };

  if (!current) return <NoProject />;

  return (
    <div className="space-y-6">
      <PlanControls plan={plan} onChange={setPlan} />
      <PageHeader
        testId="master-plan-header"
        title="Master Plan"
        description="Review a brief-based draft or import a tailored implementation plan."
        actions={
          <div className="flex gap-2">
            {plan && diffRows && (
              <Button data-testid="view-master-diff-btn" variant="outline" onClick={() => setDiffOpen(true)}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <GitCompare size={15} /> View Changes
              </Button>
            )}
            {plan && (
              <Button data-testid="copy-master-btn" variant="outline"
                onClick={() => copyMarkdown(masterPlanToMarkdown(current, plan), "Master plan")}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <Copy size={15} /> Copy
              </Button>
            )}
            {plan && (
              <Button data-testid="export-master-btn" variant="outline"
                onClick={() => downloadMarkdown(planFilename(current, "master-plan"), masterPlanToMarkdown(current, plan))}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <Download size={15} /> Export Markdown
              </Button>
            )}
            <Button data-testid="generate-master-btn" onClick={generate} disabled={generating}
              className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">
              {generating ? <RefreshCw size={15} className="animate-spin" /> : plan ? <RefreshCw size={15} /> : <Sparkles size={15} />}
              {generating ? "Generating…" : plan ? "Regenerate" : "Generate Master Plan"}
            </Button>
          </div>
        }
      />

      <CostEstimate kind="regenerate" tier="cheap" projectId={current.id} version={costVersion} />

      {loading ? (
        <div className="text-sm text-[#64748B]">Loading…</div>
      ) : !plan ? (
        <EmptyState
          testId="no-master-plan"
          icon={FileText}
          title="No master plan yet"
          description="Generate the master implementation plan from the project brief. It defines the stack, architecture, and a numbered roadmap."
          action={<Button data-testid="empty-generate-master" onClick={generate} disabled={generating} className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]"><Sparkles size={15} /> Generate Master Plan</Button>}
        />
      ) : (
        <div className="space-y-6">
          <Panel testId="master-summary-panel" title="Summary">
            <p className="text-sm leading-relaxed text-[#94A3B8]">{plan.summary}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {plan.recommended_stack.map((s) => (
                <span key={s} className="rounded-md border border-[#282E3A] bg-[#0D0F12] px-2 py-0.5 font-mono text-xs text-[#38BDF8]">{s}</span>
              ))}
            </div>
          </Panel>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Panel title="Architecture & Structure">
              <div className="space-y-5">
                <TextSection title="Folder structure" text={plan.folder_structure} />
                <ListSection title="Component architecture" items={plan.component_architecture} />
                <ListSection title="Page & section structure" items={plan.page_structure} />
                <ListSection title="Data model" items={plan.data_model} />
              </div>
            </Panel>
            <Panel title="Animation & Experience">
              <div className="space-y-5">
                <ListSection title="Animation architecture" items={plan.animation_architecture} />
                <TextSection title="Reusable scroll-chapter pattern" text={plan.scroll_chapter_pattern} />
                <TextSection title="Desktop & mobile strategy" text={plan.responsive_strategy} />
                <TextSection title="Image & performance strategy" text={plan.image_performance_strategy} />
              </div>
            </Panel>
            <Panel title="Quality & Delivery">
              <div className="space-y-5">
                <ListSection title="Accessibility requirements" items={plan.accessibility_requirements} />
                <TextSection title="Form & enquiry strategy" text={plan.form_strategy} />
                <ListSection title="SEO requirements" items={plan.seo_requirements} />
              </div>
            </Panel>
            <Panel title="Git, Testing & Deployment">
              <div className="space-y-5">
                <TextSection title="Git checkpoint strategy" text={plan.git_checkpoint_strategy} />
                <TextSection title="Testing strategy" text={plan.testing_strategy} />
                <TextSection title="Deployment strategy" text={plan.deployment_strategy} />
              </div>
            </Panel>
          </div>

          <Panel testId="roadmap-panel" title="Implementation Roadmap" subtitle={`${plan.roadmap.length} numbered tasks with recommended model tiers`} noPad>
            <Accordion type="multiple" className="divide-y divide-[#1E232D]">
              {plan.roadmap.map((r) => (
                <AccordionItem key={r.number} value={`t-${r.number}`} className="border-0 px-4" data-testid={`roadmap-item-${r.number}`}>
                  <AccordionTrigger className="py-3 hover:no-underline">
                    <div className="flex flex-1 items-center justify-between gap-3 pr-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="font-mono text-xs text-[#64748B]">#{String(r.number).padStart(2, "0")}</span>
                        <span className="truncate text-sm font-medium text-[#E2E8F0]">{r.title}</span>
                      </div>
                      <TierBadge tier={r.recommended_tier} />
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pb-4">
                    <div className="space-y-3 rounded-md border border-[#282E3A] bg-[#0D0F12] p-3">
                      <div>
                        <div className="text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">Objective</div>
                        <p className="mt-1 text-sm text-[#94A3B8]">{r.objective}</p>
                      </div>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <div>
                          <div className="text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">Files</div>
                          <div className="mt-1 space-y-0.5 font-mono text-xs text-[#38BDF8]">
                            {r.files.map((f) => <div key={f} className="truncate">{f}</div>)}
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">Dependencies</div>
                          <div className="mt-1 font-mono text-xs text-[#94A3B8]">{r.dependencies.length ? r.dependencies.map((d) => `#${d}`).join(", ") : "none"}</div>
                        </div>
                      </div>
                      <div>
                        <div className="text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">Acceptance criteria</div>
                        <ul className="mt-1 space-y-1">
                          {r.acceptance_criteria.map((a, i) => (
                            <li key={i} className="flex gap-2 text-sm text-[#94A3B8]"><span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-emerald-400" />{a}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Panel>
        </div>
      )}

      <PlanDiffDialog open={diffOpen} onOpenChange={setDiffOpen} title="Master Plan — changes since last version" rows={diffRows} />
    </div>
  );
}
