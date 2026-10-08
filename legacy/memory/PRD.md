# ProjectPilot — PRD

## Original Problem Statement
Build "ProjectPilot", an AI-assisted coding orchestration workspace. Workflow: project brief → master implementation plan → AI delegation plan → task queue → model assignment → code-edit request → temporary preview branch → live preview → lint/type-check/build verification → diff review → human approval → Git commit/merge. Must NEVER autonomously merge/deploy without explicit human approval. Model tiers: Local, Cheap, Expensive, Human Review. All providers MOCKED in MVP (no real LLM calls, no API keys). Premium dark developer-tool aesthetic.

## User Choices
- Stack: React (JSX) + FastAPI + MongoDB (not Next.js/TS — env constraint)
- Fully mocked providers, no keys
- Core flow prioritized; no auth (single-developer workspace)
- Sample "Contractor Storage Yard Website" fully seeded

## Architecture
- Backend: FastAPI. `models.py` (Pydantic, uuid-string ids, ISO timestamps), `providers.py` (modular `ModelProvider` interface + Local/Cheap/Expensive mock providers + deterministic verification runner), `seed_data.py` (generic plan generators + hand-authored sample), `server.py` (all `/api` routes + startup auto-seed).
- Frontend: React Router, Tailwind dark theme, lucide-react icons, recharts, sonner toasts. `lib/api.js` client, `lib/store.jsx` current-project context, `lib/ui.jsx` status/tier badges. Sidebar + TopBar layout. 13 pages.
- DB collections: projects, master_plans, delegation_plans, tasks, diffs, verifications, previews, model_runs, activity, settings.

## User Personas
- Solo developer orchestrating AI-assisted builds while minimizing expensive-model spend.

## Core Requirements (static)
- Human approval gate before any merge/deploy (enforced: approve endpoint 400s unless task passed verification).
- 4 model tiers with cost tracking. Mocked providers only.
- Plans shown for review, never auto-executed.

## Implemented (2026-06)
- Dashboard: stat cards, current project/task, pending approvals w/ inline approve, recent runs, tasks-by-status/tier, verify failures, recent activity, quick actions.
- Projects: list + create dialog (all brief fields) + "Load Sample Brief" + delete.
- Project Overview: workflow progress, brief, metadata.
- Master Plan: full sections + numbered roadmap accordion; generate/regenerate.
- Delegation Plan: tier counts + per-task accordion (prompt, allowed/blocked files, verify cmds, commit msg); materialize to queue.
- Task Queue: filterable table, inline tier selector, create task.
- Task Details: Run AI Edit (mock diff + preview branch + model run), Run Verification (lint/type/build), Diff review, Approve & Merge / Reject, Launch Preview, tier config.
- Live Preview: launch/stop sessions, desktop/mobile mock render.
- Verification, Git & Diffs (branches + diff viewer + approvals), Usage & Cost (charts + budget), Activity Logs (timeline), Settings (prefs + tier reference + reseed).
- Tested: 100% backend (15 pytest) + frontend, no issues.

## Backlog
- P1: Split server.py into routers; add TaskUpdate/SettingsUpdate Pydantic schemas (currently accept arbitrary dict).
- P2: Real ModelProvider implementations behind the interface; multi-user auth; export plans to markdown.
