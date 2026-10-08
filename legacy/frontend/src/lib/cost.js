// Informational cost estimation using the existing mock credit system.
// 1 credit = $0.001 (mock). Bounds mirror the token ranges in backend/providers.py.
export const CREDITS_PER_USD = 1000;

export const toCredits = (usd) => Math.round((usd || 0) * CREDITS_PER_USD);

// Representative min/max USD cost per tier (derived from mock provider token ranges).
const TIER_BOUNDS = {
  local: { min: 0, max: 0 },
  cheap: { min: 0.0006, max: 0.0032 },
  expensive: { min: 0.0112, max: 0.063 },
  human_review: { min: 0, max: 0 },
};

// kind: 'edit' | 'regenerate' | 'build'
export function estimateAction(kind, tier) {
  let bounds;
  if (kind === "build") bounds = { min: 0, max: 0 };
  else if (kind === "regenerate") bounds = TIER_BOUNDS.cheap; // deterministic mock planner
  else bounds = TIER_BOUNDS[tier] || TIER_BOUNDS.cheap;
  return { minCr: toCredits(bounds.min), maxCr: toCredits(bounds.max) };
}

export const KIND_LABEL = {
  edit: "AI edit",
  regenerate: "plan regeneration",
  build: "verification build",
};
