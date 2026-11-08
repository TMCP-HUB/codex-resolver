# Playwright Dogfood Setup

## Install

```bash
npm install -D @playwright/test
npx playwright install --with-deps chromium
```

## Suggested scripts

```json
{
  "scripts": {
    "qa:dogfood": "playwright test tests/dogfood",
    "qa:dogfood:headed": "playwright test --headed",
    "qa:dogfood:report": "playwright show-report"
  }
}
```

## Suggested structure

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

## Minimum checks

- home page loads
- no critical console errors
- no failed critical requests
- mobile CTA visible
- forms validate correctly
- forms submit correctly
- key routes do not 404
- major images load

## Cloudflare workflow

Recommended:

1. deploy preview
2. run Playwright against preview URL
3. upload artifacts to GitHub Actions

## Artifact policy

Store:

- screenshots on failure
- traces on failure
- HTML report
- markdown QA summary

Do not commit generated artifacts to git unless intentionally preserving evidence.
