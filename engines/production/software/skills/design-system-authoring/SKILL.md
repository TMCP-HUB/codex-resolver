---
name: design-system-authoring
description: Establish or apply a bounded visual design contract when UI or design-system work is in scope.
---

# Design System Authoring

## Purpose

Use this skill before UI work, visual refactors, landing page redesigns, admin interface cleanup, or when creating or updating a project `DESIGN.md`.

## Goal

Turn vague visual direction into a small design contract that agents can follow without inventing random spacing, colors, shadows, layouts, or component behavior.

This skill is not for cloning another brand.
It is for creating a project-specific visual operating system.

## When to use

Use this skill when the task includes any of:

- page layout
- UI components
- Tailwind classes
- spacing, radius, shadows, borders, or motion
- forms, wizards, cards, tables, modals, menus, or admin screens
- dark mode or theme presets
- making a design more polished, premium, clean, stylish, mobile-first, or conversion-focused

## Inputs

Collect only what is needed:

- product type
- target audience
- primary user action
- brand mood
- existing colors or assets
- current UI problems
- framework and component stack
- pages or components in scope
- non-negotiable product constraints

If exact values are missing, use practical defaults consistent with the approved scope and avoid scattering one-off choices. Record them in `DESIGN.md` when the task actually needs or updates that durable design contract; otherwise use the existing appropriate design source or bounded implementation note.

## Execution contract

- Source/design mode uses supplied direction or authorized relevant repository/design reads; it does not itself prove rendered behavior.
- Implementation requires the authorized write path. Runtime, browser or accessibility observation is needed only for an accepted claim that requires it, on an available capable surface. Missing required evidence is `NOT_PROVEN`; use a separate capable observer when independent acceptance is required.

## Required output

For design-system work that actually needs a durable design contract, create or update `DESIGN.md` in the product repository; otherwise reuse the existing source or record only the decisions needed for the task.

For implementation work, include a short design compliance note:

- design source used
- page or component type
- tokens or components touched
- visual risks
- actual evidence and checks performed, when needed for the accepted claim

## Design contract layers

A useful `DESIGN.md` should define these layers, in this order:

1. Product and brand direction
2. Page type priorities
3. Design tokens
4. Layout rules
5. Component rules
6. Responsive behavior
7. Motion rules
8. Accessibility baseline
9. Do and don't rules
10. Visual QA checklist

Do not start with random component styling before the direction and tokens are clear.

## Page type decision table

| Page type | Main job | Layout priority | Common failure to avoid |
|---|---|---|---|
| Marketing landing | Convert and build trust | Hero, proof, CTA, service clarity | Generic SaaS look with weak local trust |
| Service page | Explain one offer and push contact | Clear sections, local proof, repeated CTA | Long text wall with no action path |
| Location page | Rank and feel local | Local headings, service cards, area proof | Duplicate city pages with thin copy |
| Calculator or wizard | Guide step-by-step input | One decision per step, sticky summary | Too many controls visible at once |
| Admin dashboard | Manage data fast | Density, scan speed, safe actions | Pretty cards that hide operational state |
| Menu or catalog | Browse and choose quickly | Categories, item cards, prices, mobile readability | Desktop-first tables on phones |
| Documentation | Teach and unblock | Headings, examples, code blocks | Decorative layout fighting readability |
| Experimental brand page | Create emotion and memory | Strong art direction, controlled motion | Effects that break usability |

## Design intensity table

| Intensity | Use when | Visual behavior | Risk |
|---|---|---|---|
| Quiet | Admin, docs, data-heavy tools | Neutral colors, tight spacing, minimal effects | Can feel unfinished |
| Professional | Local services, B2B, lead gen | Strong CTA, trust blocks, clean sections | Can become generic |
| Premium | Hospitality, high-ticket services | More whitespace, larger type, richer imagery | Can reduce information density |
| Expressive | Bars, events, creative brands | Strong color, motion, custom hero | Can hurt clarity |
| Experimental | Visual demos, art-heavy concepts | Unusual layout and effects | Can break performance and mobile UX |

Choose one primary intensity and one secondary accent. Do not mix all modes on one page.

## Token minimum

Every project `DESIGN.md` should define at least:

| Token group | Required decisions |
|---|---|
| Color | background, surface, text, muted text, border, primary CTA, secondary CTA, danger, success |
| Typography | font family, heading scale, body size, line height, label style |
| Spacing | base scale, section padding, card padding, grid gap, form gap |
| Radius | button, card, modal, input, pill |
| Shadow | none, soft, elevated, overlay |
| Border | default border color, strong border color, divider behavior |
| Motion | duration, easing, allowed effects, reduced-motion fallback |
| Breakpoints | mobile, tablet, desktop behavior |

## Practical spacing scale

Use a small spacing scale unless the project already has one:

| Name | Value | Use |
|---|---:|---|
| 0 | 0 | Reset and flush edges |
| 1 | 4px | Tiny icon and label gaps |
| 2 | 8px | Compact internal gaps |
| 3 | 12px | Button and form micro spacing |
| 4 | 16px | Default component padding |
| 6 | 24px | Card padding and grid gaps |
| 8 | 32px | Section internal spacing |
| 12 | 48px | Mobile section padding |
| 16 | 64px | Desktop section padding |
| 24 | 96px | Large hero rhythm only |

Avoid arbitrary values like 17px, 23px, 37px unless matching an existing system.

## Component decision table

| Component | Must define | Must not do |
|---|---|---|
| Button | hierarchy, sizes, hover, disabled, loading | invent a new style per section |
| Card | padding, radius, border, shadow, image behavior | mix 5 shadow depths on one page |
| Form | label placement, error state, helper text, focus state | hide errors or rely only on placeholder text |
| Table | density, mobile fallback, row actions, empty state | force wide tables on mobile |
| Modal | width, backdrop, close behavior, scroll behavior | create full-screen chaos without reason |
| Navigation | active state, mobile menu, CTA placement | move primary CTA unpredictably |
| Hero | headline rhythm, image or background rules, CTA group | overload with every possible message |
| Wizard | step state, back/next behavior, summary block | expose all steps at once on mobile |
| Theme switcher | tokens affected, preview behavior, persistence | change random classes outside tokens |

## Agent procedure

1. Read existing `AGENTS.md` and `DESIGN.md` if present.
2. Inspect the current UI patterns before changing files.
3. Identify the page type and design intensity.
4. Reuse existing tokens and components first.
5. If approved design-system work needs a durable design contract and none exists, create the smallest useful `DESIGN.md`; a bounded UI change does not automatically require a new document.
6. Implement with shared classes, component variants, or token mapping.
7. Avoid one-off Tailwind chains when a shared pattern should exist.
8. Check only the affected visual, interaction and responsive claims, using the smallest suitable observation; neither mobile and desktop checks nor manual human inspection are automatic.
9. Record visual risks, evidence and unproven claims.
10. A source-only observation cannot prove rendered spacing, interaction or mobile behavior. Where an accepted claim genuinely requires it, use the appropriate capable observer and surface.

## Anti-patterns

Avoid:

- copying another brand instead of defining this project
- random gradients added as decoration
- inconsistent section padding
- inconsistent card radius
- buttons with different heights for the same role
- tables that are unusable on mobile
- modals with no scroll handling
- animations that run forever or block reading
- text contrast that looks fine only on one screen
- adding a new UI library for a small styling task
- hiding unfinished controls instead of making the contract explicit

## Visual QA checklist

Before sign-off, apply only the questions relevant to the affected surface and accepted claims:

- Does the UI follow `DESIGN.md`?
- Are spacing and radius consistent across repeated components?
- Is the primary action obvious on mobile?
- Are forms usable with errors, loading, and disabled states?
- Where responsive behavior is in scope, are tables or dense layouts usable on the claimed screens?
- Does motion respect reduced-motion behavior when relevant?
- Did the change avoid unrelated visual rewrites?
- Are any new tokens or component variants documented?

## Minimal verdict format

- Design source
- Page type
- Tokens touched
- Components touched
- Responsive evidence, where claimed
- Risks
- Verdict: pass, partial, or fail
