# Presentation Completion Barrier

> Classification: **Solution Pattern — optional**. This is one way to serialize commands behind application-owned presentation completion when domain readiness and observable readiness are different. It is unnecessary when presentation is instantaneous, irrelevant to ordering, or already owned by a stronger scheduler/workflow engine.

## Problem class

The domain/runtime can finish a transition before its user-visible or externally observable presentation is actually complete. A later command that checks only domain readiness can overtake an in-flight presentation and create ordering, focus, accessibility, animation, or resource conflicts.

Core distinction:

```text
domain ready
!=
application presentation boundary ready
```

## Production trace

This pattern came from a language-transition and reader-presentation flow where the runtime had already advanced, but typed/system presentation and frontier completion were still active. New commands had to queue until the application-owned presentation lifecycle released its lease rather than relying on runtime status alone.

## Assumptions

- some presentation side effects are semantically or operationally ordered;
- domain/runtime completion can precede presentation completion;
- later commands can safely wait or queue;
- the application can expose one completion signal/lease for the relevant presentation boundary.

## Use when

Use when:

- animated/typed transitions must finish before another command starts;
- focus/inert/modal lifecycle must settle before navigation or another overlay;
- a presentation owns a publication/resource lease;
- assistive announcement commits must finish before a conflicting presentation;
- command ordering depends on what the user has actually been shown, not only domain state.

## Do not use when

Prefer a simpler design when:

- presentation is decorative and may overlap safely;
- domain state alone intentionally governs command ordering;
- all effects are coordinated by an existing statechart/actor/workflow scheduler;
- parallel presentation regions are independent and one global barrier would over-serialize them;
- blocking user commands would harm UX more than overlapping effects.

## Pattern

### 1. Name the actual completion boundary

Do not use a vague `isBusy` flag.

Define what completion means for the affected interaction, for example:

```text
render mounted
+ authored timing settled
+ acknowledgement resolved
+ owned frontier/resource released
```

Use only the conditions actually needed.

### 2. Represent presentation ownership explicitly

Possible forms:

- lease/owner ID;
- promise/future representing completion;
- state-machine phase;
- queue token;
- application-level `presentationInFlight` record.

The mechanism is secondary to having one clear owner.

### 3. Queue or reject commands according to priority policy

When a command arrives during presentation:

```text
command
→ execute now if compatible
→ otherwise queue/pending
→ or reject/cancel if stale by the time barrier opens
```

Do not automatically queue every command. Define priority/arbitration explicitly.

### 4. Drain only after full barrier release

A common bug is checking domain state too early:

```text
runtime.status == ready
→ command executes
```

when presentation still owns focus/frontier/timing.

Instead drain after the application completion signal.

### 5. Define cancellation/reset semantics

If reset, navigation, terminal shutdown, or session replacement occurs during presentation:

- abort owned waits safely;
- release resources/leases exactly once;
- mark queued commands stale/dead when their premise no longer holds;
- do not execute old pending work against a new session/state.

### 6. Keep barrier scope narrow

Use separate barriers for independent presentation domains when appropriate. One global lock can create unnecessary latency and deadlocks.

## Why it works

It makes observable completion an explicit scheduling dependency rather than hoping domain readiness implies the UI/application has finished its side effects.

## Trade-offs

- command latency can increase;
- queue/arbitration rules add state;
- a stuck presentation can block dependent work;
- one global barrier may over-serialize unrelated UI;
- cancellation and teardown need careful cleanup.

## Alternatives

Consider instead:

- make presentation purely derived/decorative and never block commands;
- actor/statechart that owns domain + presentation lifecycle together;
- per-component local sequencing with no global application barrier;
- cancel/replace prior presentation instead of waiting;
- transactional navigation/rendering framework that already guarantees ordering;
- remove authored timing if it has no product value.

## Failure modes

- runtime/domain `ready` is mistaken for full application readiness;
- command executes while prior modal/frontier/focus ownership is active;
- queued command survives reset/terminal transition and runs against stale state;
- presentation failure leaves barrier permanently occupied;
- release happens twice or not at all;
- global barrier serializes unrelated operations and creates artificial deadlocks;
- reduced-motion path skips a causal completion marker rather than only decorative timing.

## Verification

- force domain completion while presentation remains active; dependent command stays pending/rejected according to policy;
- release presentation and prove pending command drains exactly once;
- compatible independent command can proceed if policy allows;
- presentation failure/recovery cannot strand the barrier;
- reset/terminal/session replacement invalidates stale pending work;
- reduced-motion/accessibility paths preserve required completion ordering;
- no command path bypasses the declared barrier by consulting domain status alone.

## Related Core Principles

- `authority-mapping` — domain authority and presentation ownership are different roles;
- `dependency-ownership` — scheduling dependency should be explicit, not accidental;
- `irreversible-boundary-reasoning` — domain may already be committed when presentation fails;
- `anti-loop-execution` — stuck barrier/repeated retries require causal diagnosis rather than bypass patches.
