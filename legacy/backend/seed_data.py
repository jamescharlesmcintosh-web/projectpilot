"""Seed content and deterministic mock planning generators.

- build_master_plan / build_delegation_plan work for ANY project (generic template
  adapted from the brief), so the "Generate" buttons in the UI produce structured output.
- The seeded sample project ("Contractor Storage Yard Website") gets a rich, hand-authored
  master plan + delegation plan.
"""
from typing import List, Dict


# ----------------------------------------------------------------------------
# Generic generators (used by the Generate Plan buttons for any project)
# ----------------------------------------------------------------------------
def build_master_plan(project: dict) -> dict:
    ptype = project.get("project_type", "website")
    stack = [s.strip() for s in (project.get("tech_stack") or "React, TypeScript, Tailwind CSS, Framer Motion, Vite").split(",") if s.strip()]
    return {
        "summary": f"Master implementation plan for '{project['name']}' — derived from the project brief. "
                   "Scope is broken into numbered, independently verifiable roadmap tasks with recommended model tiers.",
        "recommended_stack": stack,
        "folder_structure": (
            "src/\n"
            "  components/   # reusable UI + section components\n"
            "  sections/     # page chapters\n"
            "  hooks/        # scroll + animation hooks\n"
            "  lib/          # utils, constants, content\n"
            "  styles/       # tokens, globals\n"
            "  pages/        # route entry points\n"
            "public/         # optimized imagery, fonts\n"
        ),
        "component_architecture": [
            "Layout shell (Header, Footer, ScrollProvider)",
            "Reusable ScrollChapter wrapper with sticky + parallax slots",
            "Section primitives (Hero, FeatureRow, MediaReveal, FAQ, ContactForm)",
            "Design-system atoms (Button, Badge, Field) driven by tokens",
        ],
        "page_structure": [
            "Single long-scroll landing page composed of chapters",
            "Anchored navigation to each chapter",
            "Standalone routes only where needed (privacy, terms)",
        ],
        "data_model": [
            "content.ts — editable copy + placeholder fields",
            "sections config — order, ids, media refs",
            "enquiry submission — {name, contact, message, interest}",
        ],
        "animation_architecture": [
            "Scroll progress driven by a single ScrollProvider",
            "Parallax + masked reveals via transform/opacity only",
            "Respect prefers-reduced-motion; no layout-thrashing animations",
        ],
        "scroll_chapter_pattern": (
            "Each chapter = <ScrollChapter> with a sticky viewport, a pinned background media "
            "layer, and a foreground content layer that reveals on scroll progress. Chapters are "
            "composable and reused across sections to keep the codebase DRY."
        ),
        "responsive_strategy": "Mobile-first. Chapters collapse sticky/parallax on small screens into stacked reveals. Fluid type scale.",
        "image_performance_strategy": "Responsive srcset, AVIF/WebP, lazy loading below the fold, blur-up placeholders, preconnect to media host.",
        "accessibility_requirements": [
            "WCAG AA contrast", "Full keyboard navigation", "Reduced-motion fallback",
            "Semantic landmarks + alt text", "Visible focus states",
        ],
        "form_strategy": "Progressive-enhanced enquiry form, client + server validation, honeypot spam trap, success/error states.",
        "seo_requirements": ["Semantic headings", "Meta + OpenGraph", "Sitemap + robots", "Structured data (LocalBusiness)", "Fast LCP"],
        "git_checkpoint_strategy": "One preview branch per task (preview/task-N). Commit only after verification passes and human approval.",
        "testing_strategy": "Lint + typecheck + build gate per task. Component smoke tests. Manual visual QA in live preview.",
        "deployment_strategy": f"Target: {project.get('deployment_target') or 'static host / edge CDN'}. Deploy only from approved, merged main.",
        "roadmap": [
            {"number": 1, "title": "Project scaffolding & design tokens", "objective": "Set up the app shell, tooling, and design tokens.",
             "files": ["src/styles/tokens.css", "src/lib/content.ts", "vite.config.ts"], "dependencies": [],
             "acceptance_criteria": ["App builds", "Tokens applied globally", "Lint clean"], "recommended_tier": "cheap"},
            {"number": 2, "title": "Layout shell & navigation", "objective": "Header, footer, anchored nav, ScrollProvider.",
             "files": ["src/components/Header.tsx", "src/components/Footer.tsx", "src/hooks/useScroll.ts"], "dependencies": ["1"],
             "acceptance_criteria": ["Nav anchors scroll", "Responsive header"], "recommended_tier": "cheap"},
            {"number": 3, "title": "Reusable ScrollChapter pattern", "objective": "Build the sticky + parallax chapter primitive.",
             "files": ["src/components/ScrollChapter.tsx", "src/hooks/useParallax.ts"], "dependencies": ["2"],
             "acceptance_criteria": ["Sticky works", "Parallax smooth", "Reduced-motion honored"], "recommended_tier": "expensive"},
            {"number": 4, "title": "Hero chapter", "objective": "Cinematic hero with masked reveal + CTA.",
             "files": ["src/sections/Hero.tsx"], "dependencies": ["3"],
             "acceptance_criteria": ["LCP image optimized", "CTA visible"], "recommended_tier": "cheap"},
            {"number": 5, "title": "Content chapters", "objective": "Implement remaining scroll chapters reusing the pattern.",
             "files": ["src/sections/*.tsx"], "dependencies": ["3", "4"],
             "acceptance_criteria": ["All chapters render", "Copy uses placeholders"], "recommended_tier": "cheap"},
            {"number": 6, "title": "Enquiry form", "objective": "Accessible enquiry form with validation + states.",
             "files": ["src/sections/Contact.tsx", "src/lib/validate.ts"], "dependencies": ["2"],
             "acceptance_criteria": ["Validation works", "Success/error states"], "recommended_tier": "cheap"},
            {"number": 7, "title": "Accessibility & performance review", "objective": "Audit a11y, motion, and Core Web Vitals.",
             "files": ["src/**"], "dependencies": ["4", "5", "6"],
             "acceptance_criteria": ["AA contrast", "Good LCP/CLS", "Keyboard complete"], "recommended_tier": "expensive"},
            {"number": 8, "title": "Final production review & merge", "objective": "Human review of business claims + approval to merge.",
             "files": ["src/lib/content.ts"], "dependencies": ["7"],
             "acceptance_criteria": ["No invented claims", "Approved by human"], "recommended_tier": "human_review"},
        ],
    }


def build_delegation_plan(project: dict, master: dict) -> dict:
    tasks = []
    for r in master.get("roadmap", []):
        tier = r["recommended_tier"]
        tasks.append({
            "number": r["number"],
            "name": r["title"],
            "description": r["objective"],
            "recommended_tier": tier,
            "model_prompt": (
                f"You are implementing task #{r['number']} ('{r['title']}') for the project '{project['name']}'. "
                f"Objective: {r['objective']} Only modify the allowed files. Do not invent business, pricing, "
                f"security, or availability claims — use editable placeholders. Return a unified diff."
            ),
            "allowed_files": r["files"],
            "blocked_files": ["src/lib/content.ts"] if tier != "human_review" else [],
            "expected_output": "Unified diff limited to allowed files that satisfies the acceptance criteria.",
            "verification_commands": ["npm run lint", "npm run typecheck", "npm run build"],
            "git_commit_message": f"feat(task-{r['number']}): {r['title'].lower()}",
            "dependencies": r["dependencies"],
            "requires_human_approval": tier in ("expensive", "human_review"),
        })
    return {"tasks": tasks}


# ----------------------------------------------------------------------------
# Rich hand-authored sample: Contractor Storage Yard Website
# ----------------------------------------------------------------------------
SAMPLE_PROJECT = {
    "name": "Contractor Storage Yard Website",
    "description": "Cinematic, scroll-driven marketing site for a secure contractor storage facility.",
    "brief": (
        "Build a high-resolution, cinematic, scroll-driven website for a secure contractor storage facility "
        "offering shipping-container storage and individually fenced private storage plots. The website should feel "
        "rugged, trustworthy, professional, and local. It should target contractors, tradespeople, builders, "
        "landscapers, mechanics, and small businesses that need space for tools, equipment, materials, trailers, "
        "vehicles, pallets, and job-site supplies.\n\n"
        "The website should use high-resolution photography, cinematic image transitions, parallax, sticky sections, "
        "masked image reveals, text animation, and smooth scroll chapters. It must not use 3D models, Three.js, WebGL, "
        "virtual tours, or rotating objects.\n\n"
        "The website should include a hero section, container-storage chapter, fenced-plot chapter, contractor benefits, "
        "security and access, storage options, location, FAQs, contact information, enquiry form, pricing placeholders, "
        "dimensions, availability, access hours, and a final call to action.\n\n"
        "Do not invent prices, security features, access hours, dimensions, availability, cameras, 24/7 access, "
        "electricity, water, or insurance details. Use editable placeholders unless information is confirmed."
    ),
    "repo_url": "git@github.com:acme/contractor-storage-yard.git",
    "local_path": "~/dev/contractor-storage-yard",
    "tech_stack": "React, TypeScript, Tailwind CSS, Framer Motion, Vite",
    "project_type": "marketing_site",
    "deployment_target": "Static host + edge CDN (approval-gated)",
    "primary_developer": "You",
    "status": "active",
}

SAMPLE_MASTER = {
    "summary": (
        "Master implementation plan for the Contractor Storage Yard Website. A single long-scroll, cinematic "
        "landing experience built from reusable scroll chapters. No 3D/WebGL. All business, pricing, security, "
        "dimension, and availability details remain editable placeholders until confirmed."
    ),
    "recommended_stack": ["React", "TypeScript", "Vite", "Tailwind CSS", "Framer Motion", "Lenis (smooth scroll)"],
    "folder_structure": (
        "src/\n"
        "  components/      ScrollChapter, MediaReveal, Header, Footer, Button, Field\n"
        "  sections/        Hero, ContainerStorage, FencedPlots, Benefits, Security,\n"
        "                   StorageOptions, Location, Pricing, FAQ, Contact, FinalCTA\n"
        "  hooks/           useSmoothScroll, useParallax, useReveal\n"
        "  lib/             content.ts (all editable copy + PLACEHOLDERS), seo.ts\n"
        "  styles/          tokens.css, globals.css\n"
        "public/images/     optimized AVIF/WebP photography\n"
    ),
    "component_architecture": [
        "ScrollProvider wraps the app and drives a single smooth-scroll instance",
        "ScrollChapter: sticky viewport + pinned media layer + revealing foreground",
        "MediaReveal: masked image reveal driven by scroll progress",
        "Section primitives compose ScrollChapter (Hero, ContainerStorage, FencedPlots, ...)",
        "Design atoms (Button, Badge, Field) read from tokens.css",
    ],
    "page_structure": [
        "1. Hero", "2. Container-Storage chapter", "3. Fenced-Plot chapter", "4. Contractor Benefits",
        "5. Security & Access", "6. Storage Options", "7. Location", "8. Pricing (placeholders)",
        "9. Dimensions / Availability / Access hours (placeholders)", "10. FAQs",
        "11. Contact + Enquiry form", "12. Final Call To Action",
    ],
    "data_model": [
        "content.ts: hero, chapters[], benefits[], faqs[], contact, PLACEHOLDERS{pricing,dimensions,accessHours,availability,security}",
        "Enquiry: { name, business, phone, email, interest: 'container'|'plot', message }",
        "SEO: { title, description, ogImage, localBusiness{} }",
    ],
    "animation_architecture": [
        "Single smooth-scroll (Lenis) instance; components subscribe to scroll progress",
        "Parallax + masked reveals via transform/opacity only (GPU-friendly)",
        "Text animation on chapter entry (staggered fade/translate)",
        "Sticky pinned chapters release cleanly; NO 3D, WebGL, Three.js, or rotating objects",
        "prefers-reduced-motion disables parallax + reveals, content stays fully visible",
    ],
    "scroll_chapter_pattern": (
        "ScrollChapter is the reusable spine of the site. Each chapter mounts a sticky full-viewport stage with a "
        "pinned background media layer and a foreground content layer. As scroll progress advances 0→1 the media "
        "parallaxes and the foreground text reveals via mask/opacity. Chapters accept media, eyebrow, heading, body, "
        "and CTA props so every section reuses one tested primitive."
    ),
    "responsive_strategy": (
        "Mobile-first. On small screens, sticky pinning and heavy parallax degrade to lightweight stacked reveals to "
        "protect performance and scroll comfort. Fluid type scale, tap-friendly targets, single-column chapters."
    ),
    "image_performance_strategy": (
        "High-res photography exported to AVIF/WebP with responsive srcset. LCP hero image preloaded; below-fold media "
        "lazy-loaded with blur-up placeholders. Media host preconnect. Budget: keep hero LCP < 2.5s on 4G."
    ),
    "accessibility_requirements": [
        "WCAG AA contrast on all text over imagery (scrims/gradients as needed)",
        "Full keyboard navigation + skip-to-content",
        "prefers-reduced-motion honored across all animations",
        "Semantic landmarks, descriptive alt text, labelled form fields",
        "Visible focus rings; no keyboard traps in sticky chapters",
    ],
    "form_strategy": (
        "Accessible enquiry form with client + server validation, honeypot spam trap, explicit interest selector "
        "(container vs fenced plot), and clear success/error states. No data stored beyond the submission record."
    ),
    "seo_requirements": [
        "Unique title + meta description", "OpenGraph + Twitter cards", "LocalBusiness structured data (placeholders)",
        "Sitemap + robots.txt", "Semantic heading hierarchy", "Fast Core Web Vitals",
    ],
    "git_checkpoint_strategy": (
        "Trunk = main. Every task runs on its own preview branch preview/task-N. Commits are created only after "
        "verification passes; merge to main requires explicit human approval. Never auto-merge or auto-deploy."
    ),
    "testing_strategy": "Per-task gate: ESLint + tsc + vite build. Reduced-motion snapshot check. Manual visual QA in live preview across desktop + mobile.",
    "deployment_strategy": "Deploy only from approved, merged main to the static host + edge CDN. Human-review gate before any production deploy.",
    "roadmap": [
        {"number": 1, "title": "Scaffold app, tooling & design tokens", "objective": "Vite + React + TS + Tailwind, base tokens, content.ts skeleton with placeholders.",
         "files": ["vite.config.ts", "src/styles/tokens.css", "src/styles/globals.css", "src/lib/content.ts"], "dependencies": [],
         "acceptance_criteria": ["App builds & runs", "Tokens applied globally", "content.ts exports typed placeholders"], "recommended_tier": "cheap"},
        {"number": 2, "title": "Smooth scroll + layout shell", "objective": "ScrollProvider (Lenis), Header with anchored nav, Footer.",
         "files": ["src/components/ScrollProvider.tsx", "src/hooks/useSmoothScroll.ts", "src/components/Header.tsx", "src/components/Footer.tsx"], "dependencies": ["1"],
         "acceptance_criteria": ["Smooth scroll active", "Anchor nav jumps to chapters", "Responsive header"], "recommended_tier": "cheap"},
        {"number": 3, "title": "ScrollChapter + MediaReveal primitives", "objective": "Reusable sticky+parallax chapter and masked image reveal driven by scroll progress.",
         "files": ["src/components/ScrollChapter.tsx", "src/components/MediaReveal.tsx", "src/hooks/useParallax.ts", "src/hooks/useReveal.ts"], "dependencies": ["2"],
         "acceptance_criteria": ["Sticky pin/release clean", "Parallax GPU-only", "Reduced-motion disables effects", "No 3D/WebGL"], "recommended_tier": "expensive"},
        {"number": 4, "title": "Hero chapter", "objective": "Cinematic hero: masked reveal, headline text animation, primary CTA.",
         "files": ["src/sections/Hero.tsx"], "dependencies": ["3"],
         "acceptance_criteria": ["LCP image preloaded", "Headline animates on load", "CTA anchors to enquiry"], "recommended_tier": "cheap"},
        {"number": 5, "title": "Container-storage & fenced-plot chapters", "objective": "Two flagship chapters reusing ScrollChapter with distinct media + copy placeholders.",
         "files": ["src/sections/ContainerStorage.tsx", "src/sections/FencedPlots.tsx"], "dependencies": ["3", "4"],
         "acceptance_criteria": ["Both chapters reuse ScrollChapter", "Dimensions/availability are placeholders"], "recommended_tier": "cheap"},
        {"number": 6, "title": "Benefits, Security & Storage Options chapters", "objective": "Contractor benefits, security & access, and storage options sections.",
         "files": ["src/sections/Benefits.tsx", "src/sections/Security.tsx", "src/sections/StorageOptions.tsx"], "dependencies": ["3"],
         "acceptance_criteria": ["No invented security/access claims", "Placeholders where unconfirmed"], "recommended_tier": "cheap"},
        {"number": 7, "title": "Location, Pricing & details placeholders", "objective": "Location chapter + editable pricing/dimensions/access-hours/availability placeholders.",
         "files": ["src/sections/Location.tsx", "src/sections/Pricing.tsx"], "dependencies": ["3"],
         "acceptance_criteria": ["All pricing/dimension/hours values are clearly-marked placeholders", "No invented numbers"], "recommended_tier": "human_review"},
        {"number": 8, "title": "FAQs & enquiry form", "objective": "Accessible FAQ accordion + validated enquiry form with interest selector.",
         "files": ["src/sections/FAQ.tsx", "src/sections/Contact.tsx", "src/lib/validate.ts"], "dependencies": ["2"],
         "acceptance_criteria": ["FAQ keyboard-accessible", "Form validates + shows states", "Honeypot present"], "recommended_tier": "cheap"},
        {"number": 9, "title": "Final CTA + SEO + metadata", "objective": "Final call-to-action chapter, meta tags, OpenGraph, LocalBusiness structured data (placeholders).",
         "files": ["src/sections/FinalCTA.tsx", "src/lib/seo.ts", "index.html"], "dependencies": ["4"],
         "acceptance_criteria": ["Meta + OG present", "Structured data uses placeholders", "Final CTA anchors to enquiry"], "recommended_tier": "cheap"},
        {"number": 10, "title": "Accessibility, motion & performance review", "objective": "Audit AA contrast, reduced-motion, keyboard flow, and Core Web Vitals.",
         "files": ["src/**"], "dependencies": ["4", "5", "6", "7", "8", "9"],
         "acceptance_criteria": ["AA contrast over imagery", "Reduced-motion complete", "Good LCP/CLS/INP"], "recommended_tier": "expensive"},
        {"number": 11, "title": "Final production review & approval to merge", "objective": "Human review of all business/pricing/security claims; approve merge to main.",
         "files": ["src/lib/content.ts"], "dependencies": ["10"],
         "acceptance_criteria": ["Zero invented business claims", "All placeholders confirmed or retained", "Human approves merge"], "recommended_tier": "human_review"},
    ],
}


def sample_delegation() -> dict:
    return build_delegation_plan(SAMPLE_PROJECT, SAMPLE_MASTER)
