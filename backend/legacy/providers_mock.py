"""Modular mock model providers. Real providers can implement ModelProvider later.

No real LLM calls are made in the MVP. Every provider is deterministic + mocked.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict
import random
import hashlib


@dataclass
class ModelInput:
    prompt: str
    task_id: str = ""
    task_title: str = ""
    tier: str = "cheap"
    allowed_files: List[str] = field(default_factory=list)
    blocked_files: List[str] = field(default_factory=list)


@dataclass
class ModelOutput:
    content: str
    diff_files: List[Dict]
    summary: str
    model_name: str
    tier: str
    tokens_in: int
    tokens_out: int
    cost: float
    latency_ms: int


# Cost per 1k tokens by tier (mock pricing)
TIER_META = {
    "local": {"model_name": "local/qwen2.5-coder-7b", "price_in": 0.0, "price_out": 0.0, "label": "Local"},
    "cheap": {"model_name": "cheap/gpt-mini-mock", "price_in": 0.0005, "price_out": 0.0015, "label": "Cheap"},
    "expensive": {"model_name": "expensive/claude-opus-mock", "price_in": 0.015, "price_out": 0.03, "label": "Expensive"},
    "human_review": {"model_name": "human/manual-gate", "price_in": 0.0, "price_out": 0.0, "label": "Human Review"},
}


def _seeded_rng(*parts: str) -> random.Random:
    h = hashlib.sha256("::".join(parts).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def _make_diff(rng: random.Random, files: List[str], title: str) -> List[Dict]:
    if not files:
        files = ["src/components/Section.tsx"]
    out = []
    for f in files[:5]:
        adds = rng.randint(6, 48)
        dels = rng.randint(0, 14)
        hunk = (
            f"@@ -1,{max(dels,1)} +1,{adds} @@\n"
            f"+// {title}\n"
            f"+export function generated() {{\n"
            f"+  // implemented by mock provider\n"
            f"+  return true;\n"
            f"+}}\n"
            + "".join(f"-// removed line {i}\n" for i in range(dels))
        )
        out.append({"path": f, "additions": adds, "deletions": dels, "hunk": hunk})
    return out


class ModelProvider(ABC):
    tier: str = "cheap"

    @abstractmethod
    def generate(self, input: "ModelInput") -> "ModelOutput":  # noqa: A002
        ...

    def _build(self, input: ModelInput) -> ModelOutput:
        meta = TIER_META[self.tier]
        rng = _seeded_rng(self.tier, input.task_id or input.prompt, input.task_title)
        tokens_in = len(input.prompt.split()) * rng.randint(2, 6) + rng.randint(120, 400)
        tokens_out = rng.randint(300, 1800)
        cost = round((tokens_in / 1000.0) * meta["price_in"] + (tokens_out / 1000.0) * meta["price_out"], 5)
        latency = rng.randint(400, 1200) if self.tier == "local" else rng.randint(1200, 5200)
        diff = _make_diff(rng, input.allowed_files, input.task_title or "Edit")
        content = (
            f"[{meta['label']} provider] Applied changes for: {input.task_title or 'edit request'}.\n"
            f"Touched {len(diff)} file(s) within allowed scope. Blocked files respected."
        )
        summary = f"{sum(d['additions'] for d in diff)} additions / {sum(d['deletions'] for d in diff)} deletions across {len(diff)} files"
        return ModelOutput(
            content=content, diff_files=diff, summary=summary,
            model_name=meta["model_name"], tier=self.tier,
            tokens_in=tokens_in, tokens_out=tokens_out, cost=cost, latency_ms=latency,
        )


class LocalMockProvider(ModelProvider):
    tier = "local"

    def generate(self, input: ModelInput) -> ModelOutput:
        return self._build(input)


class CheapMockProvider(ModelProvider):
    tier = "cheap"

    def generate(self, input: ModelInput) -> ModelOutput:
        return self._build(input)


class ExpensiveMockProvider(ModelProvider):
    tier = "expensive"

    def generate(self, input: ModelInput) -> ModelOutput:
        return self._build(input)


_REGISTRY = {
    "local": LocalMockProvider(),
    "cheap": CheapMockProvider(),
    "expensive": ExpensiveMockProvider(),
}


def get_provider(tier: str) -> ModelProvider:
    return _REGISTRY.get(tier, _REGISTRY["cheap"])


def run_verification_checks(rng_seed: str, commands: List[str], force_fail: bool = False) -> List[Dict]:
    """Deterministic mock lint/typecheck/build runner."""
    rng = _seeded_rng("verify", rng_seed)
    results = []
    labels = {"lint": "ESLint", "typecheck": "tsc", "type": "tsc", "build": "vite build", "test": "vitest"}
    for cmd in commands or ["npm run lint", "npm run typecheck", "npm run build"]:
        key = next((k for k in labels if k in cmd.lower()), "check")
        fail = force_fail and key in ("typecheck", "type", "build")
        # small chance of failure otherwise (deterministic)
        if not force_fail:
            fail = rng.random() < 0.12 and key != "lint"
        dur = rng.randint(300, 4200)
        if fail:
            out = f"$ {cmd}\n✗ {labels.get(key,'check')} failed\nerror TS2322: Type 'string' is not assignable to type 'number'.\n  at src/components/Hero.tsx:42:7"
        else:
            out = f"$ {cmd}\n✓ {labels.get(key,'check')} passed cleanly ({dur}ms)"
        results.append({"name": key, "command": cmd, "status": "failed" if fail else "passed", "output": out, "duration_ms": dur})
    return results
