# Capture on GET, Consume on POST

> Classification: **Solution Pattern — optional**. This is one proven way to protect one-time link semantics from automated navigation/prefetch. It is not required for every tokenized URL or authentication flow.

## Problem class

A one-time token arrives in a URL. Email scanners, link previewers, browser prefetchers, or other automated agents may perform GET requests before the user acts. If GET directly consumes the token or commits a consequential state change, automation can spend user intent.

## Production trace

This pattern came from a production one-time-link flow where token-bearing GETs had to be treated as potentially automated. The stable design separated safe token capture from explicit one-time consumption and removed the raw token from ordinary browser-visible navigation before the consequential mutation.

## Assumptions

- a one-time or consequential credential/action arrives through a URL;
- automated GET/prefetch is plausible;
- the application can hold short-lived protected transient state or issue an opaque continuation handle;
- an explicit same-origin mutation/confirmation step is acceptable;
- the state change is consequential enough that scanner-triggered consumption matters.

## Use when

Use when:

- magic links, invitations, activation links, destructive confirmations, or one-time grants can be consumed by GET;
- the environment is known to scan/prefetch links;
- token exposure in URL history/referrers/analytics should be reduced before ordinary app loading;
- one-time consumption should correspond to explicit user intent.

## Do not use when

Prefer another design when:

- GET is truly safe and repeatable;
- the token is not one-time and automated GET has no meaningful consequence;
- the provider/protocol already supplies equivalent scanner-resistant intent semantics;
- a user-entered code or another flow is simpler;
- introducing transient state costs more than the actual risk.

## Pattern

### 1. Receive token-bearing GET

Perform only bounded parsing/shape/expiry checks necessary to determine whether safe capture may proceed.

Do not perform the irreversible exchange or consequential mutation here.

### 2. Capture transiently

Move the credential into a server-protected transient slot or exchange it for an opaque continuation handle with short expiry and replay limits.

The capture step itself must not grant the final capability if that would recreate the same problem under another name.

### 3. Redirect to a clean URL

Remove the raw token from the normal browser-visible path before ordinary resources, analytics, and subsequent navigation load where practical.

### 4. Obtain explicit mutation intent

Require the user/client to cross a protected mutation boundary, commonly a same-origin POST with the project's normal intent/CSRF/origin protections.

The exact mechanism is architecture-specific.

### 5. Consume exactly once

At the authoritative boundary:

- revalidate transient state;
- perform the one-time exchange/mutation;
- clear or invalidate the captured state;
- return the authoritative outcome.

### 6. Define replay and expiry

Repeated GETs may recreate only safe capture semantics. Replayed/expired consume attempts must fail or reconcile according to the domain contract.

## Why it works

It separates navigation from mutation. Automated agents can inspect the link without automatically crossing the consequential boundary, while the raw credential is removed before becoming ordinary page state.

## Trade-offs

- extra route/state transition;
- one additional interaction or automatic same-origin POST step;
- transient storage/cookie/session semantics become security-sensitive;
- more browser-flow cases to verify;
- scanners with active form-submission behavior may require a stronger model.

## Alternatives

Consider instead:

- user-entered one-time code;
- server-issued confirmation handle with explicit UI approval;
- provider-native scanner protection;
- non-one-time signed link where GET has no irreversible meaning;
- immediate exchange only in an environment where automatic fetch is reliably excluded.

## Failure modes

- GET still calls the consume mutation;
- capture itself grants the final authority;
- raw token leaks to logs, analytics, referrer, JS, or page markup unnecessarily;
- transient state is long-lived or replayable;
- POST lacks the project's normal intent/origin protection;
- redirect includes the token again;
- repeated capture creates multiple independent consumable grants.

## Verification

- automated/repeated GET does not consume the one-time action;
- clean continuation URL contains no raw token;
- one valid explicit mutation consumes exactly once;
- expired/replayed transient state fails safely;
- cross-origin/invalid-intent consume attempt is rejected according to project policy;
- no ordinary page resource/analytics event receives the raw token;
- scanner/prefetch simulation covers the environment actually targeted.

## Related Core Principles

- `security-property-calibration` — defines which scanner/adversary behavior is in scope;
- `irreversible-boundary-reasoning` — separates safe navigation from one-time commit;
- `authority-mapping` — identifies the authoritative consume boundary;
- `evidence-and-authority` — prevents a clean URL or successful redirect from being overclaimed as full security proof.
