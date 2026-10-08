"""Validated public contracts. State and evidence are never client-writable."""
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, model_validator

def now_iso(): return datetime.now(timezone.utc).isoformat()
def new_id(): return str(uuid4())
Tier = Literal['auto', 'local', 'cheap', 'expensive', 'human_review']
MODEL_TIERS = ['auto', 'local', 'cheap', 'expensive', 'human_review']
class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
class ProjectCreate(Strict):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default='', max_length=3000)
    brief: str = Field(default='', max_length=30000)
    repo_url: str = Field(default='', max_length=1000)
    local_path: str = Field(default='', max_length=1000)
    tech_stack: str = Field(default='HTML, CSS, JavaScript', max_length=500)
    project_type: str = 'website'
    deployment_target: str = ''
    primary_developer: str = 'You'
    status: Literal['active', 'paused', 'archived', 'completed'] = 'active'
class ProjectUpdate(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=3000)
    brief: str | None = Field(default=None, max_length=30000)
    tech_stack: str | None = Field(default=None, max_length=500)
    status: Literal['active', 'paused', 'archived', 'completed'] | None = None
class TaskCreate(Strict):
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(default='', max_length=12000)
    tier: Tier = 'auto'
    allowed_files: list[str] = Field(default_factory=lambda: ['**'])
    blocked_files: list[str] = Field(default_factory=list)
    verification_commands: list[str] = Field(default_factory=list, max_length=10)
    git_commit_message: str = Field(default='', max_length=240)
    requires_human_approval: Literal[True] = True
    number: int | None = Field(default=None, ge=1)
    model_prompt: str = Field(default='', max_length=30000)
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=lambda: ['The requested behavior works in the preview.'], min_length=1, max_length=30)
    @model_validator(mode='after')
    def scope_conflict(self):
        if set(self.allowed_files) & set(self.blocked_files): raise ValueError('A path cannot be both allowed and blocked')
        return self
class TaskUpdate(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=12000)
    model_prompt: str | None = Field(default=None, max_length=30000)
    acceptance_criteria: list[str] | None = Field(default=None, min_length=1, max_length=30)
    verification_commands: list[str] | None = Field(default=None, max_length=10)
    allowed_files: list[str] | None = None
    blocked_files: list[str] | None = None
class SettingsUpdate(Strict):
    developer_name: str = Field(default='You', min_length=1, max_length=120)
    default_tier: Tier = 'auto'
    auto_verify: bool = True
    require_approval_before_merge: Literal[True] = True
    monthly_budget_usd: float = Field(default=0, ge=0, le=100000)
    ollama_model: str = Field(default='', max_length=160)
    max_output_tokens: int = Field(default=4096, ge=256, le=16384)
    max_context_chars: int = Field(default=24000, ge=4000, le=60000)
    max_attempts: int = Field(default=3, ge=1, le=5)
    paid_enabled: bool = False
    standard_model: str = Field(default='', max_length=160)
    advanced_model: str = Field(default='', max_length=160)
    max_run_cost_usd: float = Field(default=0.25, gt=0, le=100)
class AssignTierBody(Strict):
    tier: Tier
class RunEditBody(Strict):
    prompt: str | None = Field(default=None, max_length=30000)
    quote_id: str | None = None
class FileChange(Strict):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    path: str = Field(min_length=1, max_length=500)
    content: str | None = Field(default=None, max_length=500000)
class ImportChanges(Strict):
    summary: str = Field(default='Imported changes', max_length=2000)
    files: list[FileChange] = Field(min_length=1, max_length=200)
class Approval(Strict):
    candidate_hash: str = Field(min_length=1)
    verification_id: str = Field(min_length=1)
    checked_criteria: list[int]
    note: str = Field(default='', max_length=2000)
class HumanReview(Strict):
    checked_criteria: list[int]
    note: str = Field(min_length=1, max_length=3000)
class PlanTask(Strict):
    number: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=240)
    objective: str = Field(min_length=1, max_length=12000)
    files: list[str] = Field(default_factory=lambda: ['**'])
    dependencies: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(min_length=1, max_length=30)
    recommended_tier: Tier = 'auto'
    verification_commands: list[str] = Field(default_factory=list, max_length=10)
class PlanImport(Strict):
    summary: str = Field(min_length=1, max_length=6000)
    roadmap: list[PlanTask] = Field(min_length=1, max_length=50)
class RestoreBody(Strict):
    commit_hash: str = Field(pattern=r'^[a-f0-9]{40}$')
