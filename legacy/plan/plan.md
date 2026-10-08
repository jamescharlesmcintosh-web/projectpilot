# ProjectPilot — Full Breakdown & Forward Plan

## 1. The Original Ask (what was requested)

ProjectPilot is an AI-assisted coding orchestration workspace. A developer describes a
project, the system produces a master plan and an AI delegation plan, work flows through a
task queue where each task is assigned to a model tier, edits are proposed on preview
branches, checks are run, diffs are reviewed, and **a human approves before anything merges
or deploys**. The system must never merge or deploy on its own.

The requested workflow, end to end:
Project brief → master implementation plan → AI delegation plan → task queue → model
assignment → code-edit request → temporary preview branch → live preview → lint/type-check/
build verification → diff review → human approval → Git commit/merge.

Requested application areas: Dashboard, Projects, Project overview, Master plan, Delegation
plan, Task queue, Task details, Live preview workspace, AI edit panel, Verification results,
Git branches & diffs, Usage & cost tracking, Project state & activity logs, Settings.

Requested model tiers: **Local**, **Cheap**, **Expensive**, **Human review** — with all
providers mocked for the MVP (no real API keys, no real model calls) behind a provider
interface that real models can be plugged into later.

Requested look: a premium, serious, dark developer-tool aesthetic (graphite/charcoal,
slate panels, electric-blue active state, green = passed, amber = pending approval, red =
errors only, purple = expensive-model work), monospace for code/branches/IDs, restrained
and uncluttered — not a generic admin dashboard.

### Decisions already agreed (recorded so they can be revisited)
- Built on the existing React + FastAPI + MongoDB stack (not Next.js/TypeScript).
- Model providers fully mocked; no real model calls or keys.
- No authentication — single-developer workspace.
- The sample **"Contractor Storage Yard Website"** project is pre-seeded with a full master
  plan, delegation plan, and task queue so the app is explorable immediately.

---

## 2. What Has Been Built (done & verified)

All 14 areas exist and are wired to a live backend. Verified end-to-end by automated testing.

**Core workflow (fully working):**
- **Dashboard** — active projects, current project/task, tasks by status, tasks by model
  tier, pending approvals (with inline approve), recent model runs, verification failures,
  estimated vs actual spend, preview sessions, recent activity, and the six quick actions.
- **Projects** — list + create form with every requested field (name, description, brief,
  repo URL, local path, stack, type, deployment target, primary developer, status), plus a
  one-click "Load Sample Brief".
- **Project Overview** — brief, metadata, and a visual workflow-progress tracker.
- **Master Plan** — generate/regenerate a full plan (stack, folder structure, component
  architecture, pages, data model, animation architecture, reusable scroll-chapter pattern,
  responsive/image/accessibility/form/SEO strategies, git/testing/deployment strategy) and a
  numbered roadmap where each task carries objective, files, dependencies, acceptance
  criteria, and recommended tier.
- **Delegation Plan** — every task classified Local/Cheap/Expensive/Human-review with exact
  model prompt, allowed/blocked files, expected output, verification commands, commit
  message, dependencies, and whether human approval is required. Plans are shown for review,
  never auto-executed. Can be materialized into the task queue.
- **Task Queue** — filterable table, inline tier switching, manual task creation.
- **Task Details** — the AI edit panel (runs the mocked provider, produces a preview branch
  and a diff), diff review, verification (lint/type-check/build) results, and the human gate:
  Approve & Merge / Reject. Approving generates a commit hash and returns the branch to main.
- **Live Preview** — launch/stop preview sessions with a mock browser frame and desktop/
  mobile toggle.
- **Verification**, **Git & Diffs** (branches, diff viewer, approvals), **Usage & Cost**
  (charts + spend), **Activity Logs** (timeline), **Settings** (preferences, guardrails,
  model-tier reference, reset/reseed).

**Model tiers** — all four implemented with distinct mock pricing/behavior behind a single
provider interface ready for real providers later.

**Guardrail enforced** — the system refuses to merge a task that has not passed verification;
merges only happen on an explicit human approve action.

**Added since the core build:**
- Markdown export of the master and delegation plans.
- Copy-to-clipboard of either plan.
- Plan diffing — regenerating a plan opens a dialog showing exactly what changed.
- Cost guardrail — before an edit, regeneration, or build, an informational strip shows the
  estimated credit range, current available credits, and projected remaining credits. It
  never blocks or adds a confirmation step.

**Honest status notes:**
- All model activity, verification output, diffs, and costs are **mocked**. No real code is
  edited, no real repo is touched, no real model is called.
- The live preview is a **mock render**, not a real build of the target project.
- Git branches, commits, and merges are **simulated records**, not operations on a real Git
  remote.

---

## 3. What's Left / Suggested Roadmap

Grouped by intent. Each item notes whether it keeps the MVP as a polished demo or moves it
toward a real, operational tool. These are proposals to accept, reorder, or drop.

### A. Finish & polish the current MVP (keeps everything mocked)
1. **Shared credit balance** — load the mock credit balance once and share it across the
   cost strips instead of each strip fetching on its own.
2. **Copy the plan-change summary** — a button to copy what changed after a regeneration, for
   pasting into a PR description.
3. **Combined brief export** — bundle the master plan + delegation plan into one downloadable
   document.
4. **Estimate breakdown tooltip** — hover to see how each credit estimate is calculated.
5. **Bulk task actions** — run edit / verify across several queued tasks at once, still with
   the human approval gate on merges.
6. **Dependency awareness** — surface when a task's dependencies aren't merged yet, and order
   the queue accordingly.
7. **Empty-state onboarding** — a short guided path for a brand-new project with no plan yet.

### B. Make the workflow feel real (still no real model spend)
8. **Richer mock diffs** — generate more believable, file-specific diffs per task so review
   feels genuine.
9. **Verification variety** — configurable pass/fail scenarios and re-run history so the
   verify→fix→approve loop can be demonstrated convincingly.
10. **Plan versioning & history** — keep past plan versions and allow comparing any two, not
    just the latest regeneration.
11. **Activity & audit depth** — filter/search logs, and a per-task timeline of every action.

### C. Turn it into an operational tool (introduces real integrations & decisions)
> These change the product from "convincing demo" to "does real work" and each carries a
> decision the user owns.

12. **Real model providers** — plug actual models into the existing tier interface so edits
    generate real output. **Decision needed:** which providers per tier, and that this
    introduces real usage cost. (An Emergent-managed universal model key is available and
    would cover this without the user supplying their own keys.)
13. **Real Git integration** — connect a real repository so branches, diffs, commits, and
    merges act on actual code. **Decision needed:** which Git host and how repos are
    authorized.
14. **Real preview builds** — build and serve the target project for a genuine live preview,
    instead of the mock frame. This is a substantial piece of infrastructure.
15. **Real verification** — actually run lint/type-check/build against the connected repo.
16. **Multi-user & authentication** — only if this stops being a single-developer tool;
    would add accounts, roles, and per-user activity.
17. **Real spend tracking** — replace the mock credit system with actual provider metering
    once real models are connected.

---

## 4. Recommended Next Step

Proceed with **Section A (finish & polish the MVP)** plus **Section B item 8–9** to make the
demo genuinely compelling, while keeping everything mocked and key-free. Treat **Section C**
as a separate, explicitly-approved phase, because each item there introduces real cost, real
credentials, or significant new infrastructure and fundamentally changes what the app is.

## 5. Open Questions (only if they'd change the plan)
1. Should the next build round stay fully mocked (Sections A/B), or is there appetite to begin
   Section C — specifically **real model providers** and/or **real Git** — now?
2. If real models later: is the intent to use the Emergent-managed universal key (no user keys
   needed), or specific named providers per tier?

Assumptions if unanswered: continue fully mocked (Sections A and B), no authentication, single
developer, sample project retained.
