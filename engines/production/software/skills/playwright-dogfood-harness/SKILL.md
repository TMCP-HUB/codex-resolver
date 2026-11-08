# Playwright Dogfood Harness

## Purpose

Use this skill when an accepted browser/visual claim, a demonstrated coverage gap, or an explicit harness-building assignment requires reproducible Playwright evidence.

## Goal

Reuse the existing repository harness and relevant exact-candidate CI/checks first. A UI change alone does not require browser QA or harness construction. When required, browser evidence should be reproducible through the declared executable surface.

Select only evidence needed for the accepted claim or observed failure:

- screenshots
- traces
- console logs
- network failures
- viewport checks
- HTML reports
- CI artifacts

using repeatable commands.

## When to use

Use this skill when:

- an accepted browser, interaction, responsive, or visual claim needs proof not supplied by existing evidence
- an observed failure demonstrates a relevant browser-coverage gap
- the assignment explicitly authorizes building or extending the harness

The presence of UI, a preview, forms, or mobile users is not by itself an activation condition.

## Core rule

Run the smallest relevant existing browser check when browser testing is required. Scope routes, viewports, states, and behavior to the actual acceptance claim; retain necessary responsive, conversion, auth, and interaction checks.

Do not add setup, scripts, tests, visual snapshots, CI integration, reports, or screenshots by default. Extend the existing harness only for an authorized harness-building task or a demonstrated acceptance-coverage gap within scope. Screenshots and visual inspection are required only for explicit visual acceptance or diagnosis of an observed failure. Keep evidence free of credentials and real customer PII.

## Example structure for authorized harness work

```text
playwright.config.ts

tests/dogfood/
  smoke.spec.ts
  mobile.spec.ts
  forms.spec.ts
  visual.spec.ts

artifacts/dogfood/
  screenshots/
  traces/
  reports/
```

## Example scripts for authorized harness work

```json
{
  "scripts": {
    "qa:dogfood": "playwright test tests/dogfood",
    "qa:dogfood:headed": "playwright test --headed",
    "qa:dogfood:report": "playwright show-report",
    "qa:dogfood:install": "playwright install --with-deps chromium"
  }
}
```

## Claim-selected checks

Use only the sections relevant to the accepted behavior; this is not a mandatory full sweep.

### Smoke

- page loads
- no fatal console errors
- no broken assets
- no failed critical network requests

### Mobile

- no horizontal overflow
- CTA visible
- tap targets usable
- overlays usable

### Forms

- validation visible
- loading state visible
- success state visible
- error state visible
- analytics event path preserved

### Cloudflare

- Worker endpoints reachable
- Pages assets resolve correctly
- custom domain assumptions valid

## Procedure

1. Bind the accepted claim, exact candidate, affected route/viewport/state, and existing evidence.
2. Reuse relevant current CI and existing harness checks; run the smallest missing browser check.
3. Preserve required behavior and viewport proof without repeating unrelated QA.
4. Add or extend setup/scripts/tests/CI only when authorized harness work or a demonstrated in-scope coverage gap requires it.
5. Collect safe assertions, logs, or other evidence sufficient for the claim. Capture screenshots or inspect visuals only for explicit visual acceptance or diagnosis of an observed failure.
6. Return check results, exact evidence references, and limitations in the existing PR/Executor Result. No standalone report is required when that evidence suffices.

## Browser evidence

Choose evidence that proves the claim: existing test assertions and bounded viewport/geometry measurements, console or network logs, and traces where needed. Screenshots are not the default evidence or a substitute for behavior assertions. Existing check output and references in the PR/Executor Result suffice unless acceptance requires another artifact.

## Codex integration rule

If browser evidence is mandatory, use the declared available browser or existing Playwright route. Missing native screenshot tools do not themselves require a new harness or screenshots. If the mandatory route is unavailable, report the exact limitation and NOT_PROVEN; do not claim rendered/visual behavior from nonvisual evidence.

## Anti-patterns

Avoid:

- relying on manual screenshots only
- omitting a viewport or behavior required by acceptance
- ignoring relevant console/network failures
- creating giant flaky visual snapshot suites
- depending on external hosted QA tools for core verification

## Required output

Record in the existing PR/Executor Result:

- accepted claim and exact candidate
- relevant existing checks/evidence reused and focused checks actually run
- routes/viewports/states checked where required
- evidence references and limitations, including mandatory claims left NOT_PROVEN
- bounded check outcome: pass / partial / fail

Setup, scripts, generated artifacts, and a separate QA report are not required outputs unless the assignment actually calls for them. Executor evidence does not replace independent Verification or Control promotion authority.
