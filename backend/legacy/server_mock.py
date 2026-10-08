from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional

import models as M
from providers import get_provider, ModelInput, run_verification_checks, TIER_META
import seed_data as SD

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="ProjectPilot API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("projectpilot")

NO_ID = {"_id": 0}


async def log_activity(project_id: Optional[str], kind: str, message: str, meta: dict = None):
    act = M.Activity(project_id=project_id, kind=kind, message=message, meta=meta or {})
    await db.activity.insert_one(act.model_dump())
    return act


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------
@api.get("/")
async def root():
    return {"message": "ProjectPilot API", "status": "ok"}


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------
@api.get("/projects", response_model=List[M.Project])
async def list_projects():
    docs = await db.projects.find({}, NO_ID).sort("created_at", -1).to_list(500)
    return docs


@api.post("/projects", response_model=M.Project)
async def create_project(body: M.ProjectCreate):
    proj = M.Project(**body.model_dump())
    await db.projects.insert_one(proj.model_dump())
    await log_activity(proj.id, "info", f"Project created: {proj.name}")
    return proj


@api.get("/projects/{project_id}", response_model=M.Project)
async def get_project(project_id: str):
    doc = await db.projects.find_one({"id": project_id}, NO_ID)
    if not doc:
        raise HTTPException(404, "Project not found")
    return doc


@api.patch("/projects/{project_id}", response_model=M.Project)
async def update_project(project_id: str, body: M.ProjectUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = M.now_iso()
    res = await db.projects.update_one({"id": project_id}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(404, "Project not found")
    return await db.projects.find_one({"id": project_id}, NO_ID)


@api.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    await db.projects.delete_one({"id": project_id})
    for coll in ["master_plans", "delegation_plans", "tasks", "diffs", "verifications", "previews", "model_runs", "activity"]:
        await db[coll].delete_many({"project_id": project_id})
    return {"ok": True}


# --------------------------------------------------------------------------
# Master Plan
# --------------------------------------------------------------------------
@api.get("/projects/{project_id}/master-plan")
async def get_master_plan(project_id: str):
    doc = await db.master_plans.find_one({"project_id": project_id}, NO_ID)
    return doc  # may be null


@api.post("/projects/{project_id}/master-plan/generate", response_model=M.MasterPlan)
async def generate_master_plan(project_id: str):
    proj = await db.projects.find_one({"id": project_id}, NO_ID)
    if not proj:
        raise HTTPException(404, "Project not found")
    plan_dict = SD.build_master_plan(proj)
    plan = M.MasterPlan(project_id=project_id, **plan_dict)
    await db.master_plans.replace_one({"project_id": project_id}, plan.model_dump(), upsert=True)
    await db.projects.update_one({"id": project_id}, {"$set": {"has_master_plan": True, "orchestration_status": "planning", "updated_at": M.now_iso()}})
    await log_activity(project_id, "plan", f"Master plan generated ({len(plan.roadmap)} roadmap tasks)")
    return plan


# --------------------------------------------------------------------------
# Delegation Plan
# --------------------------------------------------------------------------
@api.get("/projects/{project_id}/delegation-plan")
async def get_delegation_plan(project_id: str):
    doc = await db.delegation_plans.find_one({"project_id": project_id}, NO_ID)
    return doc


@api.post("/projects/{project_id}/delegation-plan/generate", response_model=M.DelegationPlan)
async def generate_delegation_plan(project_id: str):
    proj = await db.projects.find_one({"id": project_id}, NO_ID)
    if not proj:
        raise HTTPException(404, "Project not found")
    master = await db.master_plans.find_one({"project_id": project_id}, NO_ID)
    if not master:
        raise HTTPException(400, "Generate the master plan first")
    plan_dict = SD.build_delegation_plan(proj, master)
    plan = M.DelegationPlan(project_id=project_id, **plan_dict)
    await db.delegation_plans.replace_one({"project_id": project_id}, plan.model_dump(), upsert=True)
    await db.projects.update_one({"id": project_id}, {"$set": {"has_delegation_plan": True, "updated_at": M.now_iso()}})
    await log_activity(project_id, "plan", f"Delegation plan generated ({len(plan.tasks)} delegated tasks)")
    return plan


@api.post("/projects/{project_id}/delegation-plan/materialize")
async def materialize_tasks(project_id: str):
    """Turn the delegation plan into an executable task queue (idempotent per number)."""
    plan = await db.delegation_plans.find_one({"project_id": project_id}, NO_ID)
    if not plan:
        raise HTTPException(400, "Generate the delegation plan first")
    created = 0
    for dt in plan["tasks"]:
        exists = await db.tasks.find_one({"project_id": project_id, "number": dt["number"]}, NO_ID)
        if exists:
            continue
        task = M.Task(
            project_id=project_id, title=dt["name"], description=dt["description"], tier=dt["recommended_tier"],
            allowed_files=dt["allowed_files"], blocked_files=dt["blocked_files"],
            verification_commands=dt["verification_commands"], git_commit_message=dt["git_commit_message"],
            requires_human_approval=dt["requires_human_approval"], number=dt["number"],
        )
        await db.tasks.insert_one(task.model_dump())
        created += 1
    await log_activity(project_id, "info", f"Materialized {created} task(s) into the queue")
    return {"created": created}


# --------------------------------------------------------------------------
# Tasks
# --------------------------------------------------------------------------
@api.get("/projects/{project_id}/tasks", response_model=List[M.Task])
async def list_tasks(project_id: str):
    docs = await db.tasks.find({"project_id": project_id}, NO_ID).to_list(500)
    docs.sort(key=lambda t: (t.get("number") or 999))
    return docs


@api.post("/projects/{project_id}/tasks", response_model=M.Task)
async def create_task(project_id: str, body: M.TaskCreate):
    proj = await db.projects.find_one({"id": project_id}, NO_ID)
    if not proj:
        raise HTTPException(404, "Project not found")
    if body.number is None:
        count = await db.tasks.count_documents({"project_id": project_id})
        body.number = count + 1
    task = M.Task(project_id=project_id, **body.model_dump())
    await db.tasks.insert_one(task.model_dump())
    await log_activity(project_id, "info", f"Task created: {task.title}")
    return task


@api.get("/tasks/{task_id}", response_model=M.Task)
async def get_task(task_id: str):
    doc = await db.tasks.find_one({"id": task_id}, NO_ID)
    if not doc:
        raise HTTPException(404, "Task not found")
    return doc


@api.patch("/tasks/{task_id}", response_model=M.Task)
async def update_task(task_id: str, body: dict):
    body.pop("id", None)
    body["updated_at"] = M.now_iso()
    res = await db.tasks.update_one({"id": task_id}, {"$set": body})
    if res.matched_count == 0:
        raise HTTPException(404, "Task not found")
    return await db.tasks.find_one({"id": task_id}, NO_ID)


@api.post("/tasks/{task_id}/assign-tier", response_model=M.Task)
async def assign_tier(task_id: str, body: M.AssignTierBody):
    if body.tier not in M.MODEL_TIERS:
        raise HTTPException(400, "Invalid tier")
    task = await db.tasks.find_one({"id": task_id}, NO_ID)
    if not task:
        raise HTTPException(404, "Task not found")
    await db.tasks.update_one({"id": task_id}, {"$set": {"tier": body.tier, "updated_at": M.now_iso()}})
    await log_activity(task["project_id"], "info", f"Task #{task.get('number')} tier → {body.tier}", {"task_id": task_id})
    return await db.tasks.find_one({"id": task_id}, NO_ID)


@api.post("/tasks/{task_id}/run-edit")
async def run_edit(task_id: str, body: M.RunEditBody):
    task = await db.tasks.find_one({"id": task_id}, NO_ID)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["tier"] == "human_review":
        raise HTTPException(400, "Human-review tasks are not executed by a model; they require manual work + approval.")

    provider = get_provider(task["tier"])
    prompt = body.prompt or f"Implement task: {task['title']}. {task['description']}"
    out = provider.generate(ModelInput(
        prompt=prompt, task_id=task_id, task_title=task["title"], tier=task["tier"],
        allowed_files=task.get("allowed_files", []), blocked_files=task.get("blocked_files", []),
    ))

    branch = f"preview/task-{task.get('number') or task_id[:6]}"
    diff = M.Diff(project_id=task["project_id"], task_id=task_id, branch=branch,
                  files=[M.DiffFile(**f) for f in out.diff_files], summary=out.summary)
    await db.diffs.delete_many({"task_id": task_id})
    await db.diffs.insert_one(diff.model_dump())

    run = M.ModelRun(project_id=task["project_id"], task_id=task_id, task_title=task["title"],
                     tier=task["tier"], model_name=out.model_name, tokens_in=out.tokens_in,
                     tokens_out=out.tokens_out, cost=out.cost, latency_ms=out.latency_ms)
    await db.model_runs.insert_one(run.model_dump())

    await db.tasks.update_one({"id": task_id}, {"$set": {
        "status": "running", "branch": branch, "diff_id": diff.id, "updated_at": M.now_iso()}})
    await db.projects.update_one({"id": task["project_id"]}, {"$set": {"current_branch": branch, "orchestration_status": "executing"}})
    await log_activity(task["project_id"], "edit",
                       f"AI edit run on {branch} ({TIER_META[task['tier']]['label']}, ${out.cost}) — {out.summary}",
                       {"task_id": task_id, "branch": branch})
    return {"diff": diff.model_dump(), "model_run": run.model_dump(), "content": out.content}


@api.post("/tasks/{task_id}/verify")
async def verify_task(task_id: str, force_fail: bool = False):
    task = await db.tasks.find_one({"id": task_id}, NO_ID)
    if not task:
        raise HTTPException(404, "Task not found")
    checks = run_verification_checks(task_id, task.get("verification_commands", []), force_fail=force_fail)
    status = "failed" if any(c["status"] == "failed" for c in checks) else "passed"
    ver = M.Verification(project_id=task["project_id"], task_id=task_id, status=status,
                         checks=[M.CheckResult(**c) for c in checks])
    await db.verifications.insert_one(ver.model_dump())
    new_task_status = "pending_approval" if status == "passed" else "failed"
    await db.tasks.update_one({"id": task_id}, {"$set": {
        "status": new_task_status, "latest_verification_id": ver.id, "updated_at": M.now_iso()}})
    if status == "passed":
        await db.projects.update_one({"id": task["project_id"]}, {"$set": {"orchestration_status": "awaiting_approval"}})
    await log_activity(task["project_id"], "verify" if status == "passed" else "error",
                       f"Verification {status} for task #{task.get('number')} ({len(checks)} checks)",
                       {"task_id": task_id})
    return ver.model_dump()


@api.post("/tasks/{task_id}/approve", response_model=M.Task)
async def approve_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, NO_ID)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] not in ("pending_approval", "approved"):
        raise HTTPException(400, "Task must pass verification before approval")
    import hashlib
    commit_hash = hashlib.sha1(f"{task_id}{M.now_iso()}".encode()).hexdigest()[:10]
    await db.tasks.update_one({"id": task_id}, {"$set": {
        "status": "merged", "commit_hash": commit_hash, "updated_at": M.now_iso()}})
    await db.projects.update_one({"id": task["project_id"]}, {"$set": {
        "current_branch": "main", "orchestration_status": "idle", "updated_at": M.now_iso()}})
    await log_activity(task["project_id"], "merge",
                       f"Human approved & merged task #{task.get('number')} → main (commit {commit_hash})",
                       {"task_id": task_id, "commit": commit_hash})
    return await db.tasks.find_one({"id": task_id}, NO_ID)


@api.post("/tasks/{task_id}/reject", response_model=M.Task)
async def reject_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, NO_ID)
    if not task:
        raise HTTPException(404, "Task not found")
    await db.tasks.update_one({"id": task_id}, {"$set": {"status": "rejected", "updated_at": M.now_iso()}})
    await db.projects.update_one({"id": task["project_id"]}, {"$set": {"orchestration_status": "idle"}})
    await log_activity(task["project_id"], "reject", f"Human rejected edit for task #{task.get('number')}", {"task_id": task_id})
    return await db.tasks.find_one({"id": task_id}, NO_ID)


@api.get("/tasks/{task_id}/diff")
async def get_diff(task_id: str):
    return await db.diffs.find_one({"task_id": task_id}, NO_ID)


@api.get("/tasks/{task_id}/verifications", response_model=List[M.Verification])
async def task_verifications(task_id: str):
    docs = await db.verifications.find({"task_id": task_id}, NO_ID).sort("created_at", -1).to_list(50)
    return docs


# --------------------------------------------------------------------------
# Diffs / Verifications / Preview (project-level)
# --------------------------------------------------------------------------
@api.get("/projects/{project_id}/diffs", response_model=List[M.Diff])
async def project_diffs(project_id: str):
    return await db.diffs.find({"project_id": project_id}, NO_ID).sort("created_at", -1).to_list(200)


@api.get("/projects/{project_id}/verifications", response_model=List[M.Verification])
async def project_verifications(project_id: str):
    return await db.verifications.find({"project_id": project_id}, NO_ID).sort("created_at", -1).to_list(200)


@api.get("/projects/{project_id}/previews", response_model=List[M.PreviewSession])
async def list_previews(project_id: str):
    return await db.previews.find({"project_id": project_id}, NO_ID).sort("created_at", -1).to_list(50)


@api.post("/projects/{project_id}/previews/launch", response_model=M.PreviewSession)
async def launch_preview(project_id: str, task_id: Optional[str] = None):
    proj = await db.projects.find_one({"id": project_id}, NO_ID)
    if not proj:
        raise HTTPException(404, "Project not found")
    branch = proj.get("current_branch", "main")
    await db.previews.update_many({"project_id": project_id, "status": "running"}, {"$set": {"status": "stopped"}})
    sess = M.PreviewSession(project_id=project_id, task_id=task_id, branch=branch, status="running",
                            url=f"https://preview.projectpilot.local/{project_id[:8]}/{branch}")
    await db.previews.insert_one(sess.model_dump())
    await log_activity(project_id, "preview", f"Live preview launched on {branch}", {"branch": branch})
    return sess


@api.post("/previews/{preview_id}/stop", response_model=M.PreviewSession)
async def stop_preview(preview_id: str):
    await db.previews.update_one({"id": preview_id}, {"$set": {"status": "stopped"}})
    return await db.previews.find_one({"id": preview_id}, NO_ID)


# --------------------------------------------------------------------------
# Usage / Activity
# --------------------------------------------------------------------------
@api.get("/projects/{project_id}/usage")
async def project_usage(project_id: str):
    runs = await db.model_runs.find({"project_id": project_id}, NO_ID).sort("created_at", -1).to_list(1000)
    return _usage_summary(runs)


@api.get("/usage")
async def global_usage():
    runs = await db.model_runs.find({}, NO_ID).sort("created_at", -1).to_list(2000)
    return _usage_summary(runs)


def _usage_summary(runs: list):
    by_tier = {}
    total_cost = 0.0
    total_tokens = 0
    for r in runs:
        t = r["tier"]
        by_tier.setdefault(t, {"tier": t, "runs": 0, "cost": 0.0, "tokens": 0})
        by_tier[t]["runs"] += 1
        by_tier[t]["cost"] = round(by_tier[t]["cost"] + r["cost"], 5)
        by_tier[t]["tokens"] += r["tokens_in"] + r["tokens_out"]
        total_cost += r["cost"]
        total_tokens += r["tokens_in"] + r["tokens_out"]
    return {
        "total_runs": len(runs),
        "total_cost": round(total_cost, 4),
        "total_tokens": total_tokens,
        "by_tier": list(by_tier.values()),
        "recent_runs": runs[:20],
    }


@api.get("/projects/{project_id}/activity", response_model=List[M.Activity])
async def project_activity(project_id: str):
    return await db.activity.find({"project_id": project_id}, NO_ID).sort("created_at", -1).to_list(200)


@api.get("/activity", response_model=List[M.Activity])
async def all_activity():
    return await db.activity.find({}, NO_ID).sort("created_at", -1).to_list(200)


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@api.get("/dashboard")
async def dashboard(project_id: Optional[str] = None):
    projects = await db.projects.find({}, NO_ID).sort("created_at", -1).to_list(500)
    active = [p for p in projects if p.get("status") == "active"]
    current = None
    if project_id:
        current = next((p for p in projects if p["id"] == project_id), None)
    if not current:
        current = active[0] if active else (projects[0] if projects else None)

    task_query = {"project_id": current["id"]} if current else {}
    tasks = await db.tasks.find(task_query, NO_ID).to_list(1000)

    by_status = {}
    by_tier = {}
    for t in tasks:
        by_status[t["status"]] = by_status.get(t["status"], 0) + 1
        by_tier[t["tier"]] = by_tier.get(t["tier"], 0) + 1

    pending = [t for t in tasks if t["status"] == "pending_approval"]
    failures = await db.verifications.find(
        ({"project_id": current["id"], "status": "failed"} if current else {"status": "failed"}), NO_ID
    ).sort("created_at", -1).to_list(20)
    runs = await db.model_runs.find(task_query, NO_ID).sort("created_at", -1).to_list(1000)
    previews = await db.previews.find(
        ({"project_id": current["id"]} if current else {}), NO_ID
    ).sort("created_at", -1).to_list(20)
    activity = await db.activity.find(
        ({"project_id": current["id"]} if current else {}), NO_ID
    ).sort("created_at", -1).to_list(12)

    running = next((t for t in sorted(tasks, key=lambda x: x.get("updated_at", ""), reverse=True)
                    if t["status"] in ("running", "pending_approval")), None)

    usage = _usage_summary(runs)
    est_cost = round(len([t for t in tasks if t["tier"] != "human_review"]) * 0.02, 3)

    return {
        "active_projects": active,
        "current_project": current,
        "current_task": running,
        "tasks_by_status": by_status,
        "tasks_by_tier": by_tier,
        "total_tasks": len(tasks),
        "pending_approvals": pending,
        "recent_runs": runs[:8],
        "verification_failures": failures,
        "estimated_cost": est_cost,
        "actual_cost": usage["total_cost"],
        "preview_sessions": [p for p in previews if p["status"] == "running"],
        "recent_activity": activity,
    }


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
@api.get("/settings", response_model=M.Settings)
async def get_settings():
    doc = await db.settings.find_one({"id": "global"}, NO_ID)
    if not doc:
        s = M.Settings()
        await db.settings.insert_one(s.model_dump())
        return s
    return doc


@api.patch("/settings", response_model=M.Settings)
async def update_settings(body: dict):
    body.pop("id", None)
    body["updated_at"] = M.now_iso()
    await db.settings.update_one({"id": "global"}, {"$set": body}, upsert=True)
    return await db.settings.find_one({"id": "global"}, NO_ID)


@api.get("/tiers")
async def get_tiers():
    return {k: {**v, "tier": k} for k, v in TIER_META.items()}


# --------------------------------------------------------------------------
# Seed
# --------------------------------------------------------------------------
@api.post("/seed")
async def seed(reset: bool = False):
    existing = await db.projects.find_one({"name": SD.SAMPLE_PROJECT["name"]}, NO_ID)
    if existing and not reset:
        return {"seeded": False, "project_id": existing["id"], "message": "Sample already present"}
    if reset:
        for coll in ["projects", "master_plans", "delegation_plans", "tasks", "diffs",
                     "verifications", "previews", "model_runs", "activity"]:
            await db[coll].delete_many({})
    await _seed_sample()
    proj = await db.projects.find_one({"name": SD.SAMPLE_PROJECT["name"]}, NO_ID)
    return {"seeded": True, "project_id": proj["id"]}


async def _seed_sample():
    # sample project
    proj = M.Project(**SD.SAMPLE_PROJECT)
    proj.has_master_plan = True
    proj.has_delegation_plan = True
    proj.orchestration_status = "awaiting_approval"
    await db.projects.insert_one(proj.model_dump())

    master = M.MasterPlan(project_id=proj.id, **SD.SAMPLE_MASTER)
    await db.master_plans.insert_one(master.model_dump())

    deleg_dict = SD.sample_delegation()
    deleg = M.DelegationPlan(project_id=proj.id, **deleg_dict)
    await db.delegation_plans.insert_one(deleg.model_dump())

    # materialize tasks + create some realistic state
    for i, dt in enumerate(deleg.tasks):
        task = M.Task(
            project_id=proj.id, title=dt.name, description=dt.description, tier=dt.recommended_tier,
            allowed_files=dt.allowed_files, blocked_files=dt.blocked_files,
            verification_commands=dt.verification_commands, git_commit_message=dt.git_commit_message,
            requires_human_approval=dt.requires_human_approval, number=dt.number,
        )
        # first two tasks merged, third pending approval, fourth running, rest queued
        if i < 2:
            task.status = "merged"
            import hashlib
            task.branch = f"preview/task-{task.number}"
            task.commit_hash = hashlib.sha1(f"{task.id}{i}".encode()).hexdigest()[:10]
        elif i == 2:
            task.status = "pending_approval"
            task.branch = f"preview/task-{task.number}"
        elif i == 3:
            task.status = "running"
            task.branch = f"preview/task-{task.number}"
        await db.tasks.insert_one(task.model_dump())

        # produce diffs + model runs for executed tasks
        if i <= 3 and task.tier != "human_review":
            provider = get_provider(task.tier)
            out = provider.generate(ModelInput(prompt=dt.model_prompt, task_id=task.id,
                                                task_title=task.title, tier=task.tier,
                                                allowed_files=task.allowed_files))
            diff = M.Diff(project_id=proj.id, task_id=task.id, branch=task.branch or "main",
                          files=[M.DiffFile(**f) for f in out.diff_files], summary=out.summary)
            await db.diffs.insert_one(diff.model_dump())
            await db.tasks.update_one({"id": task.id}, {"$set": {"diff_id": diff.id}})
            run = M.ModelRun(project_id=proj.id, task_id=task.id, task_title=task.title, tier=task.tier,
                             model_name=out.model_name, tokens_in=out.tokens_in, tokens_out=out.tokens_out,
                             cost=out.cost, latency_ms=out.latency_ms)
            await db.model_runs.insert_one(run.model_dump())
            # verification for tasks 0,1,2
            if i <= 2:
                checks = run_verification_checks(task.id, task.verification_commands)
                status = "failed" if any(c["status"] == "failed" for c in checks) else "passed"
                ver = M.Verification(project_id=proj.id, task_id=task.id, status=status,
                                     checks=[M.CheckResult(**c) for c in checks])
                await db.verifications.insert_one(ver.model_dump())
                await db.tasks.update_one({"id": task.id}, {"$set": {"latest_verification_id": ver.id}})

    # a preview session
    sess = M.PreviewSession(project_id=proj.id, branch="preview/task-3", status="running",
                            url=f"https://preview.projectpilot.local/{proj.id[:8]}/preview-task-3")
    await db.previews.insert_one(sess.model_dump())

    # a couple of extra lightweight active projects for dashboard richness
    for extra in [
        {"name": "Field Service Booking App", "project_type": "web_app", "tech_stack": "React, TypeScript, FastAPI, MongoDB", "status": "active",
         "description": "Scheduling + dispatch tool for trades.", "primary_developer": "You"},
        {"name": "Portfolio Redesign", "project_type": "portfolio", "tech_stack": "Next.js, TypeScript, Tailwind", "status": "paused",
         "description": "Personal portfolio refresh.", "primary_developer": "You"},
    ]:
        p = M.Project(**extra)
        await db.projects.insert_one(p.model_dump())
        await log_activity(p.id, "info", f"Project created: {p.name}")

    await log_activity(proj.id, "plan", "Master plan generated (11 roadmap tasks)")
    await log_activity(proj.id, "plan", "Delegation plan generated (11 delegated tasks)")
    await log_activity(proj.id, "merge", "Human approved & merged task #1 → main")
    await log_activity(proj.id, "merge", "Human approved & merged task #2 → main")
    await log_activity(proj.id, "verify", "Verification passed for task #3 (3 checks)")
    await log_activity(proj.id, "preview", "Live preview launched on preview/task-3")


app.include_router(api)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    if not await db.settings.find_one({"id": "global"}):
        await db.settings.insert_one(M.Settings().model_dump())
    if not await db.projects.find_one({"name": SD.SAMPLE_PROJECT["name"]}):
        try:
            await _seed_sample()
            logger.info("Seeded sample project on startup")
        except Exception as e:  # pragma: no cover
            logger.error(f"Seed failed: {e}")


@app.on_event("shutdown")
async def _shutdown():
    client.close()
