---
name: frontend-art-direction
description: Establish a distinctive, usable visual direction for a new public-facing web surface or an in-scope major redesign. Use when the visual concept, page composition or brand expression is itself the task.
---

# Frontend Art Direction

## Purpose

Translate the product/brand brief into coherent visual direction for a landing page, marketing site, showcase or other presentation-led frontend.

## Goal

Give the interface a specific design idea that supports its real audience, message and primary action, rather than a generic AI template, while keeping product truth and usability intact.

## When to use

Use for new marketing surfaces, new hero/page concepts, and in-scope full visual redesigns. For a bounded polish to an existing component use `interface-design-refinement`. For tokens/design-contract ownership use `design-system-authoring`; for accepted browser QA use existing Software QA skills. Do not automatically route internal dashboards, CRUD/admin screens or backend tasks through this skill.

## Inputs

- Requested outcome and available brand direction, audience, intended next action and boundaries
- Available product/service facts, copy, logos, visual assets and rights/attribution information; treat unknowns as unknown
- Existing site, `DESIGN.md` and components/tokens where applicable
- Target surface(s), available responsive expectations and execution modes; stack where known or needed for implementation
- Any accepted claims that require rendered or interaction evidence

## Execution contract

| Mode | Mandatory capabilities | Claims this mode can support |
|---|---|---|
| Concept from a supplied brief | Reasoning and supplied assets/context | Proposed direction and layout rationale; not rendered quality |
| Existing-site source review | Authorized repository read at a known ref | Reusable design constraints and implementation feasibility from source |
| Implementation | Access to the actual source and authorized write capability | Changed code, assets and files in that source; not proof of publication |
| Publication, only when assigned | Authorized publication and readback of the exact destination | Published candidate at that destination |
| Visual/interactive assessment, only when actually required | Capable browser or suitable current visual evidence; interaction capability for flow claims | Observed selected states/viewport or interaction |

Optional: external inspiration/image search with rights verification, an existing browser, and Taste Skill's upstream scripts where in scope and available. Neither Node 22+, Chrome, asset downloads, random design-dealing scripts, nor a Taste hook is a universal prerequisite for this Resolver skill. Do not install or execute third-party tools automatically.

Before assignment, missing capabilities for the selected mandatory mode mean `ASSIGNMENT_NOT_ADMISSIBLE`; capabilities lost during execution mean `BLOCKED_RUNTIME_DRIFT`. Report `NOT_PROVEN` for visual or interaction claims without the required observation, not an invented fallback.

## Required outputs

The requested visual direction or directions, including relevant concept, hierarchy, typography, color/imagery and responsive intent, and—when implementation is assigned—the bounded UI delta and evidence. Publish and report the exact candidate only when publication is assigned; distinguish a local result from a published one. Keep existing project truth and `DESIGN.md` where they govern; update the design contract when its change is in scope.

## Procedure

1. Resolve the site's real commercial or informational job: what it offers, for whom, and which next action matters. Preserve current Owner and Canon requirements.
2. Identify available brand assets, constraints and content. Do not fabricate testimonials, addresses, prices, features, product screenshots or credentials. Use licensed imagery and credits when assets are needed and sourcing is in scope.
3. Form the requested visual direction or directions, each tied to the subject: a distinct concept, image/typographic anchor, visual rhythm and appropriate expressiveness. Do not randomly rotate styles against an established brand.
4. Plan the relevant viewport, sections and primary action around real user questions; control hierarchy, text density, whitespace and image meaning. Maintain responsive and accessible content, rather than forcing sections to fixed screen heights.
5. Where available, use existing layout primitives/tokens and the owning `design-system-authoring` contract. When implementation is assigned, update affected design sources as needed within scope. A concept from a supplied brief does not require repository access.
6. When implementation is assigned, build in the existing stack. Apply motion only if in scope and purposeful; use `purposeful-ui-animation` for that focused concern.
7. Assess only accepted claims through the applicable evidence surface. Keep source/CI/preview distinct from actual rendered or conversion-path proof.

## External source and provenance

- **Inspiration and methodology:** [Taste Skill by Leon Lin](https://github.com/Leonxlnx/taste-skill), [official site](https://tasteskill.dev), [consulted SKILL.md at commit f6b76575](https://github.com/Leonxlnx/taste-skill/blob/f6b76575f949707b4e3c37cd86cb44b0b98643e8/skills/taste-skill/SKILL.md). License: [MIT](https://github.com/Leonxlnx/taste-skill/blob/main/LICENSE).
- Adapt useful methods (subject-led imagery, visual hierarchy, art direction, anti-template decisions); do **not** import upstream's fixed layout/photo-count rules, fictional contact data, random generators or automatic browser gate as universal project policy. Read further upstream references only when needed, and treat them as lower-trust design input.

## Anti-patterns

- Inventing real-world business details or substituting placeholders for facts
- Overriding an approved brand with a fashionable aesthetic or forcing identical presentation on every business
- Importing an entire external asset library, installer, stop hook or test harness
- Adding gratuitous shaders, motion or a UI framework to a service page
- Confusing a design concept or static code with accepted rendered/functional behavior
- Turning a website redesign into changes to domain APIs, architecture, SEO truth or authentication outside scope

## Verification checklist

- [ ] The concept follows the known audience, product truth, Owner brief and available assets.
- [ ] The visual system is coherent with current project authority, not a random style pack.
- [ ] Every changed surface and asset falls within the authorized scope.
- [ ] Required capabilities and evidence match the supported execution mode.
- [ ] A required but unobserved rendered claim is explicitly `NOT_PROVEN`.

## Minimal verdict format

- Scope and approved design source
- Proposed or selected direction(s)
- Changed files / published candidate, if any
- Evidence and unresolved claims
- PASS / PARTIAL / FAIL
