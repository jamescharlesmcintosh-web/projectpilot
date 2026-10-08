"""Pydantic models for ProjectPilot. IDs are uuid strings; timestamps stored as ISO strings."""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


# ---- Constants ----
MODEL_TIERS = ["local", "cheap", "expensive", "human_review"]
TASK_STATUSES = ["queued", "running", "pending_approval", "approved", "merged", "rejected", "failed"]


# ---- Project ----
class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    brief: str = ""
    repo_url: str = ""
    local_path: str = ""
    tech_stack: str = ""
    project_type: str = "website"
    deployment_target: str = ""
    primary_developer: str = ""
    status: str = "active"  # active, paused, archived, completed


class Project(ProjectCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    default_branch: str = "main"
    current_branch: str = "main"
    orchestration_status: str = "idle"  # idle, planning, executing, awaiting_approval
    has_master_plan: bool = False
    has_delegation_plan: bool = False
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


# ---- Master Plan ----
class RoadmapTask(BaseModel):
    number: int
    title: str
    objective: str
    files: List[str] = []
    dependencies: List[str] = []
    acceptance_criteria: List[str] = []
    recommended_tier: str = "cheap"


class MasterPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    summary: str = ""
    recommended_stack: List[str] = []
    folder_structure: str = ""
    component_architecture: List[str] = []
    page_structure: List[str] = []
    data_model: List[str] = []
    animation_architecture: List[str] = []
    scroll_chapter_pattern: str = ""
    responsive_strategy: str = ""
    image_performance_strategy: str = ""
    accessibility_requirements: List[str] = []
    form_strategy: str = ""
    seo_requirements: List[str] = []
    git_checkpoint_strategy: str = ""
    testing_strategy: str = ""
    deployment_strategy: str = ""
    roadmap: List[RoadmapTask] = []
    created_at: str = Field(default_factory=now_iso)


# ---- Delegation Plan ----
class DelegationTask(BaseModel):
    number: int
    name: str
    description: str
    recommended_tier: str
    model_prompt: str
    allowed_files: List[str] = []
    blocked_files: List[str] = []
    expected_output: str = ""
    verification_commands: List[str] = []
    git_commit_message: str = ""
    dependencies: List[str] = []
    requires_human_approval: bool = True


class DelegationPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    tasks: List[DelegationTask] = []
    created_at: str = Field(default_factory=now_iso)


# ---- Task Queue ----
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    tier: str = "cheap"
    allowed_files: List[str] = []
    blocked_files: List[str] = []
    verification_commands: List[str] = ["npm run lint", "npm run typecheck", "npm run build"]
    git_commit_message: str = ""
    requires_human_approval: bool = True
    number: Optional[int] = None


class Task(TaskCreate):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    status: str = "queued"
    branch: Optional[str] = None
    diff_id: Optional[str] = None
    latest_verification_id: Optional[str] = None
    commit_hash: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


# ---- Diff ----
class DiffFile(BaseModel):
    path: str
    additions: int = 0
    deletions: int = 0
    hunk: str = ""


class Diff(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    task_id: str
    branch: str
    files: List[DiffFile] = []
    summary: str = ""
    created_at: str = Field(default_factory=now_iso)


# ---- Verification ----
class CheckResult(BaseModel):
    name: str
    command: str
    status: str  # passed, failed
    output: str = ""
    duration_ms: int = 0


class Verification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    task_id: str
    status: str = "running"  # running, passed, failed
    checks: List[CheckResult] = []
    created_at: str = Field(default_factory=now_iso)


# ---- Preview Session ----
class PreviewSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    task_id: Optional[str] = None
    branch: str
    status: str = "running"  # running, stopped
    url: str = ""
    created_at: str = Field(default_factory=now_iso)


# ---- Model Run (usage) ----
class ModelRun(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: str
    task_id: Optional[str] = None
    task_title: str = ""
    tier: str = "cheap"
    model_name: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    status: str = "success"
    created_at: str = Field(default_factory=now_iso)


# ---- Activity Log ----
class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    project_id: Optional[str] = None
    kind: str = "info"  # info, edit, verify, approve, reject, merge, plan, preview, error
    message: str = ""
    meta: Dict[str, Any] = {}
    created_at: str = Field(default_factory=now_iso)


# ---- Settings ----
class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "global"
    developer_name: str = "You"
    default_tier: str = "cheap"
    auto_verify: bool = True
    require_approval_before_merge: bool = True
    monthly_budget_usd: float = 50.0
    providers: Dict[str, Any] = {}
    updated_at: str = Field(default_factory=now_iso)


# ---- Request bodies ----
class AssignTierBody(BaseModel):
    tier: str


class RunEditBody(BaseModel):
    prompt: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    brief: Optional[str] = None
    repo_url: Optional[str] = None
    local_path: Optional[str] = None
    tech_stack: Optional[str] = None
    project_type: Optional[str] = None
    deployment_target: Optional[str] = None
    primary_developer: Optional[str] = None
    status: Optional[str] = None
    current_branch: Optional[str] = None
