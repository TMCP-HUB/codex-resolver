# Webapp Dogfood QA

## Purpose

Use this skill for bounded QA when an accepted Issue claim or an observed evidence gap requires browser/user-flow proof for the affected web behavior.

## Goal

Catch relevant broken flows, mobile regressions, console errors, bad assets, and conversion/auth/interaction failures with the minimum evidence sufficient for the accepted claim.

## When to use

Use this skill when:

- the frozen Issue requires browser, conversion, auth, interaction, rendered layout, or responsive behavior proof not supplied by existing evidence
- an observed failure or demonstrated coverage gap requires a focused browser investigation

A UI edit, a preview URL, or marking a task done does not by itself require dogfood QA. Reuse relevant existing exact-candidate CI and automated checks first. A simple spacing, pixel, label, or layout microfix without an explicit visual gate goes directly to Executor with relevant existing checks; do not create a duplicate QA task.

## Inputs

Collect:

- preview URL or local URL
- changed pages/components
- expected conversion path
- target devices or viewport assumptions
- known constraints

## Claim-selected flows to test

Select only affected routes, states, and devices needed by acceptance. The sections below are a checklist menu, not a full-app or full-device sweep. Preserve required conversion, auth, interaction, browser, and responsive proof.

### Navigation

- header links
- footer links
- CTA buttons
- mobile menu
- back navigation
- external review links

### Forms and calculators

- empty validation
- invalid values
- loading state
- success state
- failure state
- analytics event path
- CRM/email submission path

### UI and layout

- hero section
- sticky mobile CTA
- responsive cards/grids
- broken spacing or overflow
- inaccessible text contrast
- missing or distorted images
- placeholder assets accidentally shipped

### Technical checks

- browser console errors
- failed network requests
- incorrect API host
- Cloudflare Worker/API responses
- stale deploy or cache behavior

## Mobile-first rules

When mobile behavior is part of the affected acceptance claim, verify the relevant items:

- CTA visible without hunting
- text readable without zoom
- tap targets large enough
- no horizontal scroll
- no clipped forms or overlays
- hero content not hidden by fixed UI

## Procedure

1. Bind the accepted claim, exact candidate, and existing check evidence.
2. Select the smallest affected route, state, device/viewport, and user path needed to close the evidence gap.
3. Run the relevant existing browser check or bounded interaction, including required negative, auth, conversion, and retry behavior.
4. Check relevant console/network failures and responsive behavior where the claim requires them.
5. Use assertions, measurements, logs, or concise reproduction notes as sufficient evidence. Generate screenshots or perform visual inspection only for explicit visual acceptance or diagnosis of an observed failure.
6. Separate blockers from polish outside acceptance; report exact evidence and a bounded outcome in the existing PR/Executor Result.
7. If a mandatory route or proof is unavailable, record the limitation and NOT_PROVEN. Do not infer rendered or visual success from nonvisual checks.

## Severity levels

| Severity | Meaning |
|---|---|
| Critical | Conversion path or app functionality broken |
| High | Major UX or data problem likely affecting users |
| Medium | Visible issue with workaround |
| Low | Cosmetic or polish issue |

## Recommended evidence

- relevant existing test output and assertions
- bounded geometry/viewport measurements
- screenshots only for explicit visual acceptance or diagnosis of an observed failure
- viewport info
- console error text
- failing request URL/status
- reproduction steps
- before/after notes

## Anti-patterns

Avoid:

- omitting mobile/viewport proof when required by acceptance
- checking visuals without trying the workflow
- claiming conversion/auth/form success without evidence of the required interaction
- ignoring console errors because the UI still renders
- approving placeholder assets or broken review links
- assuming build success means UX success

## Required output

Record in the existing PR/Executor Result:

- accepted scope and exact candidate
- relevant checks/evidence reused and focused checks actually run
- devices/viewports/states checked where required
- issues found by severity and evidence references
- conversion/auth/interaction status when in scope
- limitations and mandatory claims left NOT_PROVEN
- bounded check outcome: pass / partial / fail

No mandatory screenshots, full device sweep, new tests, or standalone QA report when existing evidence suffices. Relevant baseline CI gates and independent Verifier boundaries remain unchanged; Executor checks do not grant acceptance or promotion authority.
