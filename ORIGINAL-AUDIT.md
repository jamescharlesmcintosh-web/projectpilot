**ProjectPilot — Full Source Audit and Completion Plan**

Prepared September 10, 2026. Planning deliverable only.

**ANSWER — Preserve the existing workspace interface, repair its planning and approval contracts, then add real execution through an isolated coding engine.** The uploaded project contains implementations of many demo screens and API operations, with deliberately simulated AI, verification, preview, and Git behavior. It is not yet an operational app builder. Building more convincing simulations would not advance the recommended operational version.

**BASIS —** This audit uses only `Appbuilder--main.zip`, its `memory/PRD.md`, `plan/plan.md`, application source, dependency manifests, and included test material. The user clarified that the earlier GitHub URL was a different project and should not be used. Source findings below refer to paths inside the ZIP, with starting line numbers where useful. All 123 extracted source files were compared byte-for-byte with the archive; none changed. The archive SHA-256 is `d02496e64e4f8b66aec5546c31d6622d996aaf3278974df907001404f8519687`.

**LIMITS —** This is a source and isolated-logic audit, not a deployed penetration test, browser usability test, full dependency vulnerability scan, or production load test. No app server, MongoDB instance, real provider, Git remote, or preview server was exercised. Actual operating costs, hardware capacity, production configuration, and live visual quality are UNKNOWN. Historical test reports are records supplied with the project, not freshly reproduced results. This audit makes no completion-percentage claim.

**1. Product intent and boundaries**

The recorded product is a single-developer AI coding orchestration workspace:

Project brief → master implementation plan → delegation plan → task queue → model assignment → proposed code changes → preview → verification → diff review → explicit human approval → Git commit/merge.

The approved MVP choices in the ZIP are React JSX, FastAPI, MongoDB, mocked providers, no API keys, and no authentication for the single-developer demo. Human approval before merge or deployment is a core requirement. The later `plan/plan.md` adds Markdown exports, plan comparison, and informational credit estimates; it recommends further demo work and lists operational integrations as a separate future phase.

**RECOMMENDATION —** For “finish the app,” propose an operational single-developer release while preserving a clearly separated demo mode. This is a proposed scope extension beyond the recorded mocked MVP, not evidence that real integrations were previously approved. This document authorizes no implementation, spending, account connection, merge, or deployment.

Initial operational target: generate and modify React websites and React/FastAPI web applications. Add other project profiles only when their execution, preview, and checks are implemented. The current project-type selector also offers mobile apps, e-commerce, and API services; selecting a type currently does not create a corresponding execution capability.

**2. What is worth keeping**

| Area | VERIFIED FACT from source | Assessment / recommendation |
|---|---|---|
| Workspace shell | 13 page components and routes cover projects, planning, tasks, preview, verification, Git, usage, activity, and settings. | Retain navigation and existing page structure; improve the central work screen incrementally. |
| Project records | FastAPI routes create, read, update, and delete project records using MongoDB. | Reuse CRUD and IDs; add ownership, strict validation, recovery, and execution bindings. |
| Plan presentation | Master and delegation pages display structured plans, scope, prompts, dependencies, and task criteria. | Good contract to evolve after correcting what generation and materialization actually preserve. |
| Model abstraction | `ModelProvider`, `ModelInput`, and `ModelOutput` separate mock providers from routes. | Retain mock adapters; expand the operational interface for asynchronous runs, events, cancellation, and evidence. |
| Review presentation | Diff and verification components, status badges, and approval controls exist. | Reuse presentation; replace fabricated evidence with output from the actual workspace. |
| Export and comparison | Markdown copy/download and in-browser plan comparison are implemented. | Keep them; make versions durable and comparisons stable. |
| Visual foundation | Shared primitives, dark design tokens, tier colors, responsive classes, and a mobile sidebar exist. | Preserve the visual language. Browser verification remains needed. |
| Test starting point | 15 backend test functions and historical reports are included. | Reuse useful route checks, fix the approval-test bypass, and move tests to isolated fixtures. |

Relevant source: `frontend/src/App.js`, `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/lib/markdown.js`, `backend/server.py`, `backend/providers.py`, and `backend/tests/test_projectpilot_api.py`.

**3. Verified defects and operational gaps**

Priority definitions: **P0** = must fix before trusting real execution or exposing real project data; **P1** = needed to finish the operational workflow; **P2** = maintainability or UX improvement. Priority is a recommendation, not a claim that a deployed exploit occurred.

| ID | Priority | Finding and evidence | Required outcome |
|---|---|---|---|
| A01 | P0 | The generic planner does not read `brief`; it reads `project_type` into an unused variable. Two different briefs with otherwise identical metadata produced identical plans in an isolated check. `backend/seed_data.py:14`. | Generate from approved requirements and inspected repository context. A booking app, API, and cinematic site must produce appropriately different plans. |
| A02 | P0 | Regeneration replaces the saved master plan. For the supplied sample, the hand-authored 11-task roadmap becomes the generic 8-task roadmap. `server.py:97`, `seed_data.py`. | Create a draft version, show meaningful differences, and explicitly adopt it. Preserve the prior approved version. |
| A03 | P0 | Materialization drops `model_prompt` and `dependencies`; the Task schema also lacks acceptance criteria and plan-version linkage. Run Edit falls back to title/description unless manually overridden. `server.py:135,212`; `models.py:107`. | Preserve the complete task execution contract end to end, including versioned criteria and dependency IDs. |
| A04 | P0 | Materialization skips tasks solely by existing project/task number. Changing a planned task and materializing again created zero tasks and retained the old title in the isolated check. | Reconcile an adopted plan against queued tasks; show added/changed/obsolete tasks and protect completed history. |
| A05 | P0 | Task PATCH accepts arbitrary fields except `id`; this includes `status`, `project_id`, and evidence pointers. Approval checks only status. A failed task patched to `pending_approval` reached simulated `merged` in the isolated check. `server.py:190,268`. | Restrict writable fields; derive status through validated server transitions; require matching verification and review evidence. |
| A06 | P0 | Verification accepts a task without a diff; approval does not check a verified source digest. A no-diff fixture verified and reached simulated `merged`. Rerunning an edit retains its previous verification pointer and old runs remain visible. `server.py:212,247,268`; `TaskDetails.jsx:133`. | Bind checks and approvals to the exact candidate tree or commit. Invalidate them on edits, changes to criteria, or base updates. |
| A07 | P0 | The generated first task both allows and blocks `src/lib/content.ts`. Providers receive `blocked_files` but ignore them; a blocked file was emitted in an isolated mock run. `seed_data.py:97`; `providers.py:49,69`. | Validate contradictory scopes before scheduling, enforce blocked paths independently of the model, and reject out-of-scope edits. |
| A08 | P0 before real access | The app defines no authentication/authorization checks. `/api/seed?reset=true` deletes all project-related data; startup recreates sample data when the sample name is absent. CORS defaults broadly. `server.py:479,577,587`. | Preserve no-auth only for isolated demo use. Real mode needs an authenticated owner, private worker APIs, controlled origins, and no unrestricted reseed endpoint. |
| A09 | P1 | All providers generate deterministic placeholder hunks; verification fabricates output; merge computes a synthetic hash. Preview records contain a constructed URL and the page renders `MockSite`. `providers.py`; `server.py:268,327`; `LivePreview.jsx:11,107`. | Implement real filesystem edits, checks, preview processes, Git operations, and separate deployment evidence. These are missing integrations, not failed live integrations. |
| A10 | P1 | Human-review tasks cannot run edits, their task-detail screen hides verification, and approval remains disabled unless status is `pending_approval`. There is no dedicated review-completion transition. `TaskDetails.jsx:134,228,246`. | Give review tasks explicit checklist completion, evidence, approve/reject transitions, and an appropriate review status. |
| A11 | P1 | `auto_verify` and `default_tier` are saved and displayed but not applied by edit execution or task creation. `models.py:215`; `Settings.jsx`; `TaskQueue.jsx`; `server.py:168,212`. | Make each setting govern actual behavior, or mark/remove unavailable controls. |
| A12 | P1 | Generic delegation sets approval false for local/cheap tasks, and Markdown exports “Not required,” while the recorded product requires human approval before merge. `seed_data.py:97`; `lib/markdown.js`. | Separate permission to execute from permission to merge/deploy. Express the invariant consistently. |
| A13 | P1 | Cost, tokens, and latency are simulated. The frontend invents a credit conversion, uses fixed ranges, subtracts project history from a global monthly budget, and does not filter by month. Usage queries truncate to capped run lists. `providers.py`, `lib/cost.js`, `CostEstimate.jsx`, `server.py:350`. | Store actual provider usage and dated price records; use period-correct aggregation and distinguish estimated, observed, billed, and unknown values. |
| A14 | P1 | A 5,000-word prompt fixture generated mock cost 0.01155 USD while the frontend cheap-tier maximum is 0.0032 USD. Plan regeneration displays a cost estimate although the backend planner is a deterministic function and records no model run. | Make estimates input-aware and mode-aware. These numbers demonstrate inconsistent mock calculations; they are not real provider charges. |
| A15 | P1 | The Git page retains any previously selected diff when the project changes. Task-detail URLs are keyed only by task ID while the top bar uses a separate current-project context. `GitDiffs.jsx:26`; `App.js`; `TaskDetails.jsx`. | Scope routes and all selected state to the owning project and run. Clear stale selection and reject mismatched resource ownership. |
| A16 | P1 | Execution has no durable job worker, cancellation, restart recovery, attempt IDs, or dependency scheduler. Routes write multiple collections sequentially without a durable operation record. | Add a persistent run lifecycle, atomic claims, idempotency keys, recovery, and dependency validation before introducing retries or concurrent execution. |
| A17 | P1 | On rerun, previous diffs are deleted. Plans are overwritten rather than versioned. Git branch names derive from task number; merges hardcode `main`. `server.py:97,119,212,268`. | Keep immutable run artifacts, use unique run/workspace IDs, and honor the repository's verified default branch. |
| A18 | P1 | The flow test manually patches a failed verification to `pending_approval` before testing merge. Some tests mutate the shared sample project. `test_projectpilot_api.py:143`. | Replace the bypass with deterministic pass/fail fixtures; test rejected approvals and isolate all test data. “15 passed” does not demonstrate a sound gate. |
| A19 | P2 | Each CostEstimate strip separately loads usage and settings. Several pages have no complete request error/retry path; the API client has no configured timeout. | Share cached queries, handle stale responses, and provide actionable loading/error/retry states. Saving these HTTP requests does not directly save model tokens. |
| A20 | P2 | Markdown serialization inserts the current time, so unchanged content can differ by generation timestamp. The comparison uses a full quadratic LCS table. | Compare canonical plan data, keep metadata outside semantic comparisons, and bound large diff work. |
| A21 | P1 portability | No dependency lockfile, environment example, Docker/Compose deployment definition, or CI workflow is supplied. Tests fall back to `/app/frontend/.env`; root README is only a heading. | Supply reproducible setup, supported runtime versions, lockfiles, configuration examples, isolated tests, and recovery/deployment instructions. |
| A22 | P2 / operational preparation | Create React App/CRACO and Motor are in the dependency stack. CRA is deprecated; Motor's documented deprecation date is May 14, 2026. | Plan small, isolated migrations rather than a complete framework rewrite; confirm dependency compatibility with a real build. |
| A23 | P2 | `public/index.html` has Emergent page branding and loads an external script plus PostHog initialization. | Set ProjectPilot metadata and explicitly decide what telemetry belongs in a private coding workspace. Actual captured or transmitted data was not inspected. |

A22 external basis: [React's CRA notice](https://react.dev/blog/2025/02/14/sunsetting-create-react-app) and [Motor's migration notice](https://motor.readthedocs.io/en/stable/). These support a maintenance recommendation, not a claim that the current app cannot run.

Additional source-level risks to cover in implementation: task numbers use count-plus-one without an observed uniqueness constraint; materialization checks then inserts without an observed unique index; several queries have fixed result caps with no pagination; preview launch accepts an optional task ID without checking its project; generated default verification commands assume scripts that may not exist. The ProjectPilot frontend itself defines start/build/test but no lint/typecheck scripts. It is JSX, so a missing TypeScript check should be reported as inapplicable where appropriate, never fabricated as passed.

**4. Verification performed for this audit**

Five backend Python files parsed successfully. Thirteen isolated observations were produced by running the source planning/provider functions and selected unchanged endpoint function bodies against in-memory database substitutes. No HTTP request or real database was involved.

The checks confirmed: identical plans for different briefs; 11-to-8 sample regeneration; allowed/blocked scope conflict; blocked file emitted; invalid provider fallback to cheap; missing Task contract fields; arbitrary tier accepted at task creation; mock estimate underrun; failed-verification status bypass; project reassignment through PATCH; stale task after rematerialization; previous verification retained after editing; and simulated approval without a diff.

These observations establish specific logic behavior. They do not establish production exploitability, browser rendering, end-to-end installation success, real provider compatibility, or deployment reliability. No paid AI inference was initiated by the audit probes.

**5. Recommended finished product**

The intended operational experience should be: select or create an isolated project; describe its goal; inspect its source and constraints; review a tailored plan; approve a bounded work task; watch execution and a real preview; request a targeted correction; review source changes and actual checks; explicitly approve committing/merging; separately approve deployment.

**Architecture recommendation:** retain the React interface and FastAPI/MongoDB control layer. Add one durable worker service and an adapter to OpenCode's headless server. Run each target project in its own restricted workspace. Git, verification, and preview services produce evidence that ProjectPilot displays and validates. Only the trusted approval service can use merge/deployment credentials.

The official OpenCode server documentation lists a headless HTTP API, session operations, asynchronous prompts, abort operations, diffs, and server-sent events. That makes it a plausible backend for a custom interface. **INFERENCE:** adopting that engine should require less custom agent-loop work than implementing every coding tool and session mechanism here. Integration effort and reliability are unverified until a small adapter prototype passes. [OpenCode server documentation](https://opencode.ai/docs/server/)

OpenCode documents granular allow/ask/deny permissions. ProjectPilot should apply its own policy and workspace restrictions as well. Permission configuration does not by itself prove sandbox isolation. Verify protection of other projects, host files, secrets, Git controls, and external networking before enabling real runs. [OpenCode permissions](https://opencode.ai/docs/permissions/)

Use one verified engine version and one real model connection initially. OpenCode supports configured providers and local models, but the best model for this app is UNKNOWN without task benchmarks. If an open-model-only policy is adopted, check licenses and filter the registry accordingly. Do not hardcode today's advertised model names as permanent quality rankings. [OpenCode model configuration](https://opencode.ai/docs/models/)

Git worktrees can keep different branches checked out separately. They share repository metadata; they are a workflow mechanism, not a complete execution-security boundary. Keep separate projects in separate repositories/workspaces, with additional isolation around generated code. [Git worktree documentation](https://git-scm.com/docs/git-worktree)

**6. The five upgrades that would make it a powerhouse**

| Rank | Upgrade | Concrete user benefit | Definition of done |
|---|---|---|---|
| 1 | **Project-aware planning and durable memory** | The builder understands the actual goal, retains approved decisions, and preserves successful work during revisions. | Versioned requirements and plans; task criteria linked to requirements; source fingerprints; targeted context selection; an unrelated project brief no longer produces the same roadmap. |
| 2 | **Automatic model selection with bounded escalation** | The user chooses an outcome and usage preference; the app selects an eligible model and explains any escalation. | Capability-aware registry; per-task budget/attempt limits; routing decisions logged; benchmarks show cost and accepted quality; no silent fallback to an unapproved provider. |
| 3 | **A real build-and-preview work screen** | Watch progress, see the actual app, inspect checks/diffs, and send a specific revision from one place. | Real preview tied to a candidate version; streamed progress; stop/reconnect; desktop/mobile checks; revision becomes a scoped task instead of replacing the whole project. |
| 4 | **Project isolation and recoverable checkpoints** | Every project's files, preview, changes, and source destination remain identifiable and recoverable. | Immutable source binding; separate workspaces; per-run snapshots; restore/reject path; visible repository owner/name; deliberate project combination creates a new project with recorded inputs. |
| 5 | **Quality and cost feedback that improves decisions** | Know which model/workflow actually delivers useful work at the lowest total cost. | Usage ledger includes failures and retries; accepted tasks link to checks/review; dashboard compares cost per accepted result and repair rate by task category; saved successful patterns can be reused. |

All five are recommendations for future behavior. The source does not currently implement their operational form.

**7. How to minimize usage while maintaining output quality**

**During the completion build:**

1. Use this audit plus an adopted requirements document as the handoff. Inspect and update only the relevant source map as files change.
2. Use a capable planner for architecture, task contracts, and high-risk review. Use a less costly model that meets the acceptance criteria for bounded implementation tasks. Exact model assignments should follow measured results.
3. Build one complete vertical slice before expanding providers, supported stacks, or task parallelism.
4. Keep each work item to one independently verifiable outcome. Reuse the existing components and stack. Avoid blanket rewrites, repetitive whole-repository analysis, and parallel agents editing the same files.
5. Run deterministic schema, scope, lint, build, and targeted tests before paying a model to interpret a failure. Feed a repair the relevant error, patch, source, and criteria.
6. Stop when required checks and acceptance criteria pass. Broaden testing only for a remaining risk or release gate.
7. Save a short evidence-backed handoff: files changed, criteria satisfied, checks run, unresolved issues, and next task. Keep long logs as artifacts rather than repeating them in every prompt.

**Inside the finished product:**

| Task | Proposed routing | Usage control |
|---|---|---|
| Format, extract, compare, validate schemas, calculate costs | Deterministic code | No model call. |
| Small constrained edit following an existing pattern | Lowest-cost eligible model that passes the project benchmark | Relevant files only; bounded output and tools. |
| New component or normal feature | Proven general coding model | One task context, applicable references, acceptance criteria. |
| Architecture, persistent cross-file error, complex visual work | Stronger eligible model | Include compact prior-attempt evidence; explain escalation. |
| Lint/build/tests | Actual tools in the isolated workspace | No model call unless diagnosis is needed. |
| Merge, deploy, sensitive product claims | Human decision with generated evidence | No autonomous approval. |

Proposed starting retry policy: one initial implementation, one focused repair, then one stronger-model attempt if its use is permitted. Stop sooner on a budget limit, repeated identical failure, or missing information. This is a tunable starting rule, not a proven optimum. Infrastructure failures should not automatically trigger a different expensive model.

Cache immutable repository context by content hash, plan version, and tool configuration. Reuse dependency/build caches only where environment and ownership match. Provider prompt caching is conditional on the selected provider's documented support; there is no verified caching implementation in this ZIP.

Use provider tokens and dated rates for estimated charges, then reconcile with actual billing where available. Include planning, tool-loop model calls, repairs, failed runs, previews, worker compute, storage, and image generation if added. Local inference should not be presented as zero total cost merely because it has no token invoice.

Recommended primary metric: total attributable operating cost divided by accepted tasks in a clearly defined cohort. Show failed-only cohorts as having no accepted result, rather than dividing by zero or hiding their costs. Pair that metric with task difficulty, acceptance quality, elapsed time, and human rework so cheap but poor outputs do not appear successful.

Preserve the recorded informational estimate behavior by default. Offer an explicitly configured hard-budget mode for operational runs. Independently bound attempts, runtime, output tokens, and tools to prevent unbounded loops. For a hard budget, reserve funds atomically before dispatch and reconcile at completion; describe any provider-side cancellation or final-metering uncertainty honestly.

**UNKNOWN:** exact dollar savings, cheapest qualifying model, optimal context length, and total build effort. The archive supplies simulated usage only. A small representative pilot is needed before quoting numbers.

**8. Full build plan, in dependency order**

The phases below are proposed work packages. Each phase has an exit condition; passing one does not silently authorize deployment or paid usage.

**Phase 0 — Freeze scope and make the source reproducible.**

Preserve the uploaded baseline as its own project. Adopt the intended operational scope and retain a separate demo configuration. Document supported target stacks and unsupported project types. Create a meaningful README, environment examples, runtime requirements, dependency lockfiles, and local test setup. Isolate seeded data. Capture the current UI baseline when the app can run. Keep JSX, React, FastAPI, and MongoDB; evaluate a small CRA-to-Vite migration as its own change. Plan the Motor-to-PyMongo Async update independently.

Touches: `README.md`, manifests, environment examples, test fixtures, configuration, and baseline documentation.

Exit: a clean checkout can be installed and started reproducibly; tests use disposable data; demo and real-mode configuration cannot silently mix. No real inference is needed for validation.

**Phase 1 — Repair state, scope, and approval contracts.**

Create strict request models with explicit writable fields and enumerated values. Reject unsupported tiers. Separate task kind from model selection so manual review has a real completion path. Centralize legal state transitions. Add ownership checks, project/task/run consistency, authenticated owner access for real mode, and protected settings. Restrict or remove reseed from operational mode. Resolve allowed/blocked conflicts with blocked paths taking precedence.

Replace status-based approval with evidence checks. Bind review to project, task, candidate digest, base revision, plan version, verification requirements, and actor. New edits invalidate previous verification/review. Preserve review as a mandatory merge/deployment gate regardless of provider tier.

Touches: `backend/models.py`, `backend/server.py` split into focused route/service modules, task/settings UI, and API tests.

Exit: direct PATCH cannot change project ownership or fabricate a merged task; failed/stale/no-candidate evidence cannot approve; human-review tasks can complete through their intended UI. Negative tests establish these rules.

**Phase 2 — Build truthful planning and versioned tasks.**

Introduce a generic requirements schema with optional stack-specific sections rather than forcing all projects into a scroll-site plan. Read the approved brief and permitted repository context. Keep unknown business facts explicit. Create draft plan versions without replacing approved ones. Preserve prompts, criteria, dependencies, file scopes, expected outputs, and source references in materialized tasks. Reconcile adopted changes with the queue; do not silently rewrite completed tasks. Detect dependency cycles and stale source assumptions.

Touches: planning services replacing generic `seed_data.py` logic in real mode, plan/task schemas, MasterPlan, DelegationPlan, TaskQueue, Markdown exports.

Exit: materially different fixture briefs produce appropriate plans; unchanged requirements produce no false semantic change; adopted revisions update eligible tasks while preserving history. Use fixtures for most tests and a limited live planning evaluation only after provider usage is configured.

**Phase 3 — Deliver one real execution slice.**

Add a durable worker, persistent run record, atomic task claim, idempotency key, heartbeat, timeout, and cancel/recovery behavior. Prototype the OpenCode adapter against a pinned version and its actual API schema. Connect one provider/model. Supply one project's approved task and selected context. Permit edits only inside its isolated candidate workspace; validate the resulting filesystem diff. Store the attempt, messages, tool events, usage, and resulting artifacts. Keep the mock adapter for deterministic tests.

The worker should not hold production merge/deploy credentials or broad access to unrelated projects. Store credentials server-side and prevent them from entering prompts, diffs, previews, or logs.

Touches: execution adapter, worker service, run/event schemas, workspace manager, API events, task detail screen.

Exit: one approved small task changes an actual file in the intended workspace, produces a real diff, can be cancelled, and can be reconciled after reconnect without blindly charging for a duplicate run. No merge/deployment occurs automatically.

**Phase 4 — Add real verification and live preview.**

Discover valid commands from the target project's manifest/configuration. Execute them with timeouts and resource limits. Record real exit codes, logs, environment identity, and candidate digest. Mark unavailable checks as missing or inapplicable. Serve the candidate through an isolated preview origin and bind the URL to the exact project/run/version. Add browser checks for the task's acceptance flow, desktop/mobile layout, and visible errors. Stream concise progress; keep raw logs downloadable.

Use a combined task work screen for prompt/revision, progress, preview, diff, and evidence. Preserve separate detailed pages for investigation. Clear prior project selections on navigation; ensure a deep-linked task sets or verifies its owning project. Add request cancellation, cache invalidation, and usable error recovery.

Touches: verification runner, preview lifecycle service, `TaskDetails.jsx`, `LivePreview.jsx`, Git/verification views, shared data fetching.

Exit: an intentional build error fails truthfully; a corrected candidate passes real checks; preview shows the changed app; switching projects cannot show the other project's selected diff or preview. Tests refer to the same candidate the user reviews.

**Phase 5 — Make Git, checkpoints, and approval real.**

Verify the chosen repository identity and default branch. Keep project sources independent and persist owner/name/source binding. Use candidate workspaces and snapshots for work in progress. Preserve the recorded approval-before-commit policy unless separately changed: do not introduce automatic user-repository commits merely to create checkpoints. Retain pre-approval snapshots as local/artifact history.

On explicit approval, verify the candidate and base are unchanged, create the authorized commit/merge, and store the actual Git result. If the base moved, regenerate the proposed integration, rerun required checks, and invalidate outdated approval. Handle partial failures with a durable operation record and reconciliation. Provide restore/reject paths that preserve unrelated user changes. Test conflict and wrong-project cases.

Touches: Git adapter, approval service, snapshots, audit events, GitDiffs and approval UI.

Exit: Git history contains the reviewed change; records reference the actual result; stale or failed candidates cannot merge; rollback/recovery is demonstrated on a disposable repository. Production deployment remains separately gated.

**Phase 6 — Introduce measured routing and real usage accounting.**

Add a provider registry with verified model IDs, capabilities, limits, pricing provenance, availability, and optional license restrictions. Record every attempt and all attributable usage, including failures and planning. Add accurate month/project/workspace aggregation, pagination, budget reservations if enabled, and cost uncertainty labels. Apply bounded retry/escalation policies. Initially use one task at a time; add more concurrent work only when isolated ownership and measured benefit justify it.

Benchmark a small representative set: bounded code edit, reusable component, API feature, bug repair, and a visual interaction. Evaluate actual tests plus human visual acceptance. Reuse existing successful runs where comparable; do not run expensive model tournaments on every task. Add a second provider only after the first complete workflow is stable.

Touches: provider registry, routing/usage services, CostEstimate, Usage, Settings, run logs.

Exit: cost totals reconcile to retained usage evidence; budget periods are correct; exhausted retries stop; unavailable models do not cause uncontrolled fallbacks; route changes are based on task outcomes rather than tier labels alone.

**Phase 7 — Package and validate the operational release.**

Add one deployment adapter for the first supported target profile, with explicit release approval tied to the approved artifact. Distinguish preview, committed, merged, deployed, and deployment-failed states. Provide source/plan export, backup/restore, setup diagnostics, and worker health. Replace inherited page metadata; decide telemetry intentionally. Verify mobile navigation, keyboard access, labels, error states, and reduced-motion behavior. Run the complete user journey and failure-recovery scenarios in an isolated environment.

Touches: deployment adapter, deployment/approval records, packaging, CI, documentation, final UI/accessibility corrections.

Exit: brief → adopted plan → real task → real preview/checks → explicit Git approval → explicit release approval → working artifact, with recoverable history and evidence-backed usage. Demonstrate that two projects remain independent throughout. Leave the product at review if publication has not been authorized.

**9. Proposed contracts to prevent repeat failures**

| Record | Minimum proposed information |
|---|---|
| Project | Owner, immutable source binding, verified default branch, mode, supported stack profile, workspace reference. |
| PlanVersion | Requirements/source fingerprint, full structured plan, status, parent version, adopted-by/time. |
| Task | Stable ID, plan version, task kind, prompt/objective, acceptance criteria, dependencies, allowed/blocked paths, permitted checks, routing policy. |
| RunAttempt | Project/task IDs, candidate/base identity, engine session/version, model, context fingerprint, state, budget/attempt limits, event history. |
| Verification | Candidate digest, required-check definition, actual commands/exit codes, environment fingerprint, logs/artifacts, result. |
| Approval | Human actor, action scope, candidate/base digest, plan/check identity, decision/time, invalidation reason. |
| Preview / Deployment | Project/run/version, artifact identity, URL, lifecycle/health, actual result, approval link where required. |
| Usage | Run/request identity, estimated/observed/billed distinction, token categories where available, dated rate source, attributable compute/artifact costs. |

Use additive migrations and keep existing project/task IDs. Do not dump all record redesign into one broad rewrite. One durable worker plus the existing database is the initial architectural target; introduce extra queue/cache infrastructure only for a demonstrated need.

**10. Release acceptance checklist**

1. A new brief creates a tailored plan with traceable requirements and honest unknowns.
2. A plan revision is reviewable and does not erase its approved predecessor.
3. Materialized tasks retain their prompts, criteria, dependencies, and version linkage.
4. Ineligible or blocked tasks do not execute.
5. Generated code cannot modify another project's workspace or access protected credentials.
6. Every preview, diff, and verification result identifies the same candidate.
7. Failed, stale, missing, or fabricated evidence cannot authorize a merge.
8. Human review tasks have a usable completion path.
9. Edits/verification obey settings; unavailable controls are not represented as operational.
10. Duplicate clicks, disconnects, failed workers, and repeated errors have bounded recovery behavior.
11. Git and deployment status comes from actual operations, with explicit approvals.
12. Usage includes retries/failures and reports the correct project and billing period.
13. Switching projects clears stale state and preserves independent source/history.
14. The app installs from its documented package and can restore a tested backup.

**11. Work to defer for best use of effort**

Defer richer fabricated diffs, additional mock preview scenes, bulk autonomous builds, a large agent hierarchy, many provider integrations, native mobile generation, a plugin marketplace, fine-tuning a model, and a complete UI/framework rewrite. Do not postpone the approval fixes, project isolation, truthful planning, or real execution slice in order to add these extras.

**RECOMMENDATION — first implementation milestone:** Phase 0 and Phase 1, followed by one tailored plan and one real isolated edit. This produces a trustworthy base for the remaining phases and exposes integration uncertainty early. No implementation has begun; the uploaded source remains unchanged.
