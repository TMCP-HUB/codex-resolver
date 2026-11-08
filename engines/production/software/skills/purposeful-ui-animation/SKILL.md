---
name: purposeful-ui-animation
description: Design or implement necessary web UI motion with accessible, responsive interaction behavior. Use when a task explicitly includes animation, transitions or motion-related interaction defects.
---

# Purposeful UI Animation

## Purpose

Choose whether motion should exist and, when assigned, implement it with the smallest suitable technique, preserving the interface's function and design tokens.

## Goal

Where motion is useful, specify or implement motion that gives feedback, clarifies a state change or supports spatial understanding without slowing frequent actions, distracting from content or excluding reduced-motion users.

## When to use

Use for explicitly requested animation, relevant motion refinements, or an observed in-scope interaction defect. Do not add motion automatically to every interface or create a separate animation system. `design-system-authoring` owns project motion tokens; `frontend-art-direction` owns the larger visual concept; existing web QA owns required observed behavior.

## Inputs

- Requested interaction, component/state and usage frequency
- Existing animation styles, component primitives, design tokens and framework, where known or available
- Accessibility and input modalities (touch, pointer, keyboard, reduced motion)
- Approved behavior and claim/evidence scope; available execution capabilities

## Execution contract

| Mode | Mandatory capabilities | Claim boundary |
|---|---|---|
| Motion decision/design | Model reasoning and supplied interaction description | Recommended behavior; no claim of implementation or felt quality |
| Source-level inspection | Relevant code from authorized repository or supplied files | Implementation-level constraints/defects, not actual user-perceived smoothness |
| Implementation | Access to the actual source and authorized write capability | Changed code and source-level checks; not proof of publication |
| Publication, only when assigned | Authorized publication and readback of the exact destination | Published candidate at that destination |
| Timing/interaction observation when accepted | Suitable browser/device runtime with the relevant input and state | Actual motion, interruption, reduced-motion and interaction evidence for tested conditions |

Optional: existing animation recipes, developer tools, and a library already used by the product. No automatic package installation, test suite, video/screenshot recording, browser session or new motion framework.

Before assignment, unsupported mandatory execution means `ASSIGNMENT_NOT_ADMISSIBLE`; lost capability during execution means `BLOCKED_RUNTIME_DRIFT`. If the accepted motion claim cannot be felt or observed with an appropriate runtime, record it `NOT_PROVEN`; code inspection is not equivalent.

## Required outputs

The motion decision (including justified **no animation**), affected component and known tokens, proposed reduced-motion/pointer behavior where relevant, and minimal implementation where assigned. Include the actual evidence and limitations; include the exact published candidate only if publication is assigned, and distinguish local results from published ones.

## Procedure

1. First decide **whether to animate** in light of the requested outcome. For frequent keyboard and high-throughput actions, consider immediate state changes. When motion is chosen, name its purpose, such as feedback, spatial continuity, state comprehension, creative expression or delight. If no motion better serves the outcome, explain that decision and skip motion-mechanism and timing selection; implement removal only if that work is assigned.
2. When motion is chosen or existing motion is being modified, reuse established behavior where tokens, component library and UI primitives are known or available; do not fork a second duration/easing system. A design-only decision can use the supplied interaction description and state any assumptions without repository access.
3. When motion is chosen, select or recommend the least complex suitable mechanism: CSS transition for controlled state changes; CSS animation for simple keyframed motion; Web Animations API for programmatic control; or an existing motion library when suitable, such as for gestures, springs or layout/exit transitions. Avoid adding a dependency solely for a simple fade.
4. When motion is chosen, favor compositor-friendly `transform` and `opacity`. For implementation, consider layout changes and main-thread impact when animating geometry is needed. Choose timing/easing from known established tokens or an appropriate referenced recipe, not arbitrary novelty.
5. For the chosen motion, consider interruption, reversal, repeated triggers, entry and exit as applicable. A transition should remain coherent if the user acts again before it finishes.
6. For chosen motion, specify reduced-motion behavior and appropriate hover/pointer gating where relevant. When implementation is assigned, implement those behaviors and preserve focus, keyboard and touch accessibility. Do not animate information the user needs to read or operate just for decoration.
7. Use accepted claim-specific evidence. A code diff supports a source claim; smoothness and interruption on the actual interface require suitable observation when those claims are demanded.

## External source and provenance

- **Methodology and recipes:** [Emil Kowalski's skills](https://github.com/emilkowalski/skills), [Animate SKILL.md at commit c8a79627](https://github.com/emilkowalski/skills/blob/c8a79627b59d72d764d6ab6f2c87c09a48169833/skills/animate/SKILL.md), [animation recipes](https://github.com/emilkowalski/skills/blob/c8a79627b59d72d764d6ab6f2c87c09a48169833/skills/animate/RECIPES.md), [author's course](https://animations.dev). License: [MIT](https://github.com/emilkowalski/skills/blob/main/LICENSE).
- The upstream decision order and practical patterns are reference material, not a new global normative timing table. Read only the relevant recipe if the particular component needs it.

## Anti-patterns

- Animating a frequent workflow just because animation was possible
- Using `transition: all` without considering unintended properties, intrusive layout animation or motion that blocks input
- Ignoring relevant interruption, touch/keyboard input or `prefers-reduced-motion`
- Adding a new JS animation library, renderer, test suite or QA gate without an actual requirement
- Claiming smooth runtime motion solely from CI or a CSS change

## Verification checklist

- [ ] The motion/no-motion decision fits the requested interaction and states its rationale.
- [ ] Existing component primitives and tokens are reused where applicable and available.
- [ ] Accessibility, reduced motion and input modalities are considered.
- [ ] For chosen motion, exit/interruption behavior is specified or checked as appropriate to the interaction and selected mode.
- [ ] Required runtime observation is proven or explicitly `NOT_PROVEN`.

## Minimal verdict format

- Component and motion/no-motion decision
- Technique and tokens, if relevant
- Changed files / exact candidate, if any
- Observed conditions and evidence
- PASS / PARTIAL / FAIL
