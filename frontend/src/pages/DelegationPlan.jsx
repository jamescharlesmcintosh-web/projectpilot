import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Network, Sparkles, RefreshCw, ListPlus, ShieldAlert, FileWarning, Download, Copy, GitCompare } from "lucide-react";
import api from "../lib/api";
import { useProjects } from "../lib/store";
import { delegationToMarkdown, downloadMarkdown, copyMarkdown, planFilename } from "../lib/markdown";
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

function KV({ label, children, mono }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">{label}</div>
      <div className={`mt-1 text-sm text-[#94A3B8] ${mono ? "font-mono text-xs" : ""}`}>{children}</div>
    </div>
  );
}

export default function DelegationPlan() {
  const { current, refreshCurrent } = useProjects();
  const [plan, setPlan] = useState(null);
  const [master, setMaster] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [materializing, setMaterializing] = useState(false);
  const [diffRows, setDiffRows] = useState(null);
  const [diffOpen, setDiffOpen] = useState(false);
  const [costVersion, setCostVersion] = useState(0);

  const load = useCallback(() => {
    const pid = current?.id;
    if (!pid) { setLoading(false); return () => {}; }
    let cancelled = false;
    setLoading(true);
    Promise.all([api.getDelegationPlan(pid), api.getMasterPlan(pid)])
      .then(([p, m]) => { if (!cancelled) { setPlan(p); setMaster(m); } })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.id]);

  useEffect(() => load(), [load]);

  const generate = async () => {
    if (!master) return toast.error("Generate the master plan first");
    setGenerating(true);
    try {
      const prevMd = plan ? delegationToMarkdown(current, plan) : null;
      const p = await api.generateDelegationPlan(current.id);
      setPlan(p);
      if (prevMd) {
        setDiffRows(diffLines(prevMd, delegationToMarkdown(current, p)));
        setDiffOpen(true);
      }
      refreshCurrent();
      toast.success(`Delegation plan generated — ${p.tasks.length} delegated tasks`);
      setCostVersion((v) => v + 1);
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to generate delegation plan");
    } finally {
      setGenerating(false);
    }
  };

  const materialize = async () => {
    setMaterializing(true);
    try {
      const r = await api.materializeTasks(current.id);
      toast.success(r.created > 0 ? `${r.created} task(s) added to the queue` : "Queue already up to date");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Failed");
    } finally {
      setMaterializing(false);
    }
  };

  if (!current) return <NoProject />;

  const counts = plan
    ? plan.tasks.reduce((acc, t) => ({ ...acc, [t.recommended_tier]: (acc[t.recommended_tier] || 0) + 1 }), {})
    : {};

  return (
    <div className="space-y-6">
      <PageHeader
        testId="delegation-header"
        title="AI Delegation Plan"
        description="Each task is classified by model tier to minimize expensive usage. Plans are shown for review — never executed automatically."
        actions={
          <div className="flex gap-2">
            {plan && diffRows && (
              <Button data-testid="view-delegation-diff-btn" variant="outline" onClick={() => setDiffOpen(true)}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <GitCompare size={15} /> View Changes
              </Button>
            )}
            {plan && (
              <Button data-testid="copy-delegation-btn" variant="outline"
                onClick={() => copyMarkdown(delegationToMarkdown(current, plan), "Delegation plan")}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <Copy size={15} /> Copy
              </Button>
            )}
            {plan && (
              <Button data-testid="export-delegation-btn" variant="outline"
                onClick={() => downloadMarkdown(planFilename(current, "delegation-plan"), delegationToMarkdown(current, plan))}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <Download size={15} /> Export Markdown
              </Button>
            )}
            {plan && (
              <Button data-testid="materialize-btn" variant="outline" onClick={materialize} disabled={materializing}
                className="gap-2 border-[#282E3A] bg-transparent text-[#94A3B8] hover:text-[#E2E8F0]">
                <ListPlus size={15} /> {materializing ? "Adding…" : "Add to Task Queue"}
              </Button>
            )}
            <Button data-testid="generate-delegation-btn" onClick={generate} disabled={generating}
              className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]">
              {generating ? <RefreshCw size={15} className="animate-spin" /> : plan ? <RefreshCw size={15} /> : <Sparkles size={15} />}
              {generating ? "Generating…" : plan ? "Regenerate" : "Generate Delegation Plan"}
            </Button>
          </div>
        }
      />

      <CostEstimate kind="regenerate" tier="cheap" projectId={current.id} version={costVersion} />

      {loading ? (
        <div className="text-sm text-[#64748B]">Loading…</div>
      ) : !plan ? (
        <EmptyState
          testId="no-delegation-plan"
          icon={Network}
          title="No delegation plan yet"
          description={master ? "Classify each roadmap task into Local / Cheap / Expensive / Human Review with exact prompts, allowed files, and verification commands." : "Generate the master plan first, then create the delegation plan."}
          action={<Button data-testid="empty-generate-delegation" onClick={generate} disabled={generating || !master} className="gap-2 bg-[#38BDF8] text-[#0D0F12] hover:bg-[#0EA5E9]"><Sparkles size={15} /> Generate Delegation Plan</Button>}
        />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {["auto", "local", "cheap", "expensive", "human_review"].map((t) => (
              <div key={t} data-testid={`tier-count-${t}`} className="pp-surface flex items-center justify-between rounded-lg p-3">
                <TierBadge tier={t} />
                <span className="font-mono text-lg font-semibold text-[#E2E8F0]">{counts[t] || 0}</span>
              </div>
            ))}
          </div>

          <Panel testId="delegation-list-panel" title="Delegated Tasks" subtitle="Review prompts, file scopes, and verification before execution" noPad>
            <Accordion type="multiple" className="divide-y divide-[#1E232D]">
              {plan.tasks.map((t) => (
                <AccordionItem key={t.number} value={`d-${t.number}`} className="border-0 px-4" data-testid={`delegation-item-${t.number}`}>
                  <AccordionTrigger className="py-3 hover:no-underline">
                    <div className="flex flex-1 items-center justify-between gap-3 pr-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="font-mono text-xs text-[#64748B]">#{String(t.number).padStart(2, "0")}</span>
                        <span className="truncate text-sm font-medium text-[#E2E8F0]">{t.name}</span>
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        {t.requires_human_approval && <ShieldAlert size={14} className="text-[#FBBF24]" title="Requires human approval" />}
                        <TierBadge tier={t.recommended_tier} />
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pb-4">
                    <div className="space-y-3 rounded-md border border-[#282E3A] bg-[#0D0F12] p-3">
                      <KV label="Description">{t.description}</KV>
                      <div>
                        <div className="text-[10px] font-semibold uppercase tracking-wide text-[#64748B]">Exact model prompt</div>
                        <pre className="mt-1 whitespace-pre-wrap rounded-md border border-[#282E3A] bg-[#14171D] p-2.5 font-mono text-xs leading-relaxed text-[#94A3B8]">{t.model_prompt}</pre>
                      </div>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <KV label="Allowed files" mono>
                          <div className="space-y-0.5">{t.allowed_files.map((f) => <div key={f} className="truncate text-[#4ADE80]">+ {f}</div>)}</div>
                        </KV>
                        <KV label="Blocked files" mono>
                          {t.blocked_files.length ? <div className="space-y-0.5">{t.blocked_files.map((f) => <div key={f} className="truncate text-[#F87171]"><FileWarning size={11} className="mr-1 inline" />{f}</div>)}</div> : <span className="text-[#64748B]">none</span>}
                        </KV>
                      </div>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <KV label="Expected output">{t.expected_output}</KV>
                        <KV label="Dependencies" mono>{t.dependencies.length ? t.dependencies.map((d) => `#${d}`).join(", ") : "none"}</KV>
                      </div>
                      <KV label="Verification commands" mono>
                        <div className="space-y-0.5">{t.verification_commands.map((c) => <div key={c} className="text-[#38BDF8]">$ {c}</div>)}</div>
                      </KV>
                      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                        <KV label="Git commit message" mono><span className="text-[#A78BFA]">{t.git_commit_message}</span></KV>
                        <KV label="Human approval">
                          <span className={t.requires_human_approval ? "text-[#FBBF24]" : "text-[#64748B]"}>{t.requires_human_approval ? "Required before merge" : "Not required"}</span>
                        </KV>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Panel>
        </div>
      )}

      <PlanDiffDialog open={diffOpen} onOpenChange={setDiffOpen} title="Delegation Plan — changes since last version" rows={diffRows} />
    </div>
  );
}
