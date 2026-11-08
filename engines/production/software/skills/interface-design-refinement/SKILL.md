---
name: interface-design-refinement
description: Critique and refine an existing web UI within its authorized visual and functional scope. Use for awkward hierarchy, generic AI-looking pages, inconsistent visual treatment, or explicit UI polish.
---

# Interface Design Refinement

## Purpose

Improve an existing interface using targeted critique and precise edits, without treating a visual refinement as permission to redesign the product.

## Goal

Make the selected page or component clearer, more distinctive where appropriate, and easier to use while preserving the established brand, content, interactions and existing design system.

## When to use

Use when asked to critique, polish, simplify, strengthen, adapt, or correct an existing UI or its visual hierarchy. Use `frontend-art-direction` instead for a new marketing concept or an in-scope full visual redesign. Use `design-system-authoring` for tokens and the design contract; `webapp-dogfood-qa` owns required browser-flow evidence.

## Inputs

- Exact page/component and authorized change boundary
- Existing visuals, `DESIGN.md`/tokens and brand/copy constraints, if available
- Surface job and primary user action, where known
- Relevant rendered evidence or accessible source; accepted visual claims
- Existing implementation stack and available execution capabilities, when implementation is assigned

## Execution contract

| Mode | Mandatory capabilities | Claims this mode can support |
|---|---|---|
| Design critique of supplied artifacts | Model reasoning and supplied source/screenshots | Findings about those artifacts only; not live behavior |
| Remote source review | Authorized repository read at the relevant ref | Source-level design defects, not actual rendered geometry |
| UI implementation | Access to the actual source and authorized write capability | Source edits in that source; not proof of publication |
| Publication, only when assigned | Authorized publication and readback of the exact destination | Published candidate at that destination |
| Rendered evaluation, when accepted scope requires it | Capable browser or trustworthy current visual capture for the selected page/state/viewport | Observed appearance; interaction requires actual interaction evidence |

Optional: an already installed Impeccable tool, browser inspection, screenshots, and external design references. None is a universal requirement. Reuse existing CI and browser evidence when relevant; do not automatically install Impeccable, run its hooks, open live mode, bypass agent approvals, or add tests. At the cited Impeccable version, live Apply may fall back to a local CLI with approvals and sandboxing disabled when no chat agent is polling; `IMPECCABLE_LIVE_COPY_AGENT=chat` or `off` changes that behavior. Follow the actual execution environment's permission rules and the Owner's already authorized scope.

For missing mandatory capabilities before assignment use `ASSIGNMENT_NOT_ADMISSIBLE`; for capability loss during a previously valid execution use `BLOCKED_RUNTIME_DRIFT`. If a required rendered claim is not observed, report `NOT_PROVEN` for that claim; never substitute source-only review.

## Required outputs

The in-scope critique or UI delta, the actual design source used, selected improvements, affected files/route when applicable, reused or newly observed evidence, and any unproven claim. If publication is assigned, include the exact published candidate; do not call a local result published. No new design document unless the approved change actually needs one.

## Procedure

1. Bind the requested Owner outcome and any existing visual contract. Establish what may change and what must stay.
2. Inspect only the target and adjacent components necessary to understand its hierarchy, user task, navigation, density, typography, spacing and accessibility.
3. Rank concrete improvements by user impact; distinguish usability problems from a subjective preference for a different aesthetic.
4. Select the smallest appropriate refinement move: clarify content/CTA, distill visual noise, strengthen hierarchy, tune typography/layout, adapt the affected viewport, or harden a relevant edge state.
5. Where available, reuse established tokens, components and accessible behavior. Preserve truthful business content, SEO/semantic structure, keyboard/focus patterns and data interactions.
6. When implementation is assigned, make only the authorized changes. Motion belongs to `purposeful-ui-animation` when motion itself is in scope; no automatic animation or dependency.
7. Check only the claims requiring proof using an admitted mode and available or newly gathered evidence. A rendered conclusion needs visual evidence; a working form needs interaction evidence. Record exact limitations.

## External source and provenance

- **Inspiration and workflow reference:** [Impeccable by Paul Bakaus](https://github.com/pbakaus/impeccable), [official docs](https://impeccable.style/docs), [consulted source SKILL.md at commit 687bc381](https://github.com/pbakaus/impeccable/blob/687bc381bc9091bf252c0a05303640561014a425/.agents/skills/impeccable/SKILL.md). License: [Apache-2.0](https://github.com/pbakaus/impeccable/blob/main/LICENSE).
- Its critique, polish, distill, typeset, layout, adapt and harden techniques are reference methods, not mandatory commands or a delegated source of Owner authority. Consult the smallest relevant upstream playbook on demand when accessible. No upstream installer, executable, hook, or browser overlay is bundled here.

## Anti-patterns

- Replacing an approved identity or factual copy merely to escape a familiar AI aesthetic
- Turning a narrow fix into a site-wide redesign, global detector, new tests, or new QA gate
- Assuming an upstream preference (font, layout, imagery, motion) overrides the project's Canon
- Treating a CSS diff, CI success, or static screenshot as proof of all interactions or responsive states
- Automatically executing third-party scripts, live Apply, or bypass-permission paths

## Verification checklist

- [ ] The target, applicable design authority and allowed scope are identified.
- [ ] Each change serves the requested outcome instead of importing generic visual rules.
- [ ] Existing tokens, behavior and content outside scope are preserved.
- [ ] Delivered artifacts and any required claim-specific observations have matching evidence.
- [ ] Required unavailable evidence is marked `NOT_PROVEN`, not silently claimed.

## Minimal verdict format

- Scope and design source
- Changes and exact candidate (if any)
- Evidence by accepted claim
- Remaining limitations
- PASS / PARTIAL / FAIL
