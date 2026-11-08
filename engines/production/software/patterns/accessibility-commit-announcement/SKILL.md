---
name: accessibility-commit-announcement
description: Separate streaming visual text from committed accessibility announcements when that interaction needs the pattern.
---

# Accessibility Commit Announcement

> Classification: **Solution Pattern — optional**. This is one way to make visually streaming or incrementally mutating text accessible without causing assistive technology to announce every intermediate mutation. It is not the universal accessibility strategy for all dynamic UI.

## Problem class

A UI visually streams, types, updates, or progressively builds text. If the entire streaming surface is a live region, screen readers may announce partial text repeatedly, create noise, or duplicate the final message.

The product wants:

```text
visual streaming
!=
assistive announcement stream
```

and a single meaningful announcement when the semantic message commits.

## Production trace

This pattern came from a typed system-message surface where per-grapheme DOM mutations were intentionally visual only. A separate visually-hidden live region announced the complete system line exactly once when its semantic state changed from streaming to committed.

## Assumptions

- visual incremental rendering is meaningful or desired;
- the final committed message is the primary semantic unit for announcement;
- the application can signal semantic commit independently from character/DOM mutation;
- users do not need every intermediate token announced live.

## Use when

Use when:

- text types character-by-character but should be announced as a complete message;
- a progress/status surface mutates frequently while semantic checkpoints are less frequent;
- streaming output would make `aria-live` excessively noisy;
- the application already has explicit message lifecycle states such as streaming/committed/settled.

## Do not use when

Prefer another approach when:

- each incremental update is itself semantically important;
- users need live progress at a controlled interval;
- the UI does not stream visually and can simply render/announce atomically;
- the accessibility API/framework already provides a suitable announcement primitive;
- the content is a document/prose surface that should be navigated normally rather than pushed through live-region announcements.

## Pattern

### 1. Keep the visually mutating surface out of the live region

Do not put `aria-live` on the container that receives every character/token mutation if those mutations are not meant to be announced individually.

### 2. Define a semantic lifecycle marker

Track a state such as:

```text
streaming
→ committed
→ settled
```

The exact names do not matter. What matters is that semantic commit is explicit and not inferred from arbitrary timing.

### 3. Add one dedicated announcement surface

Create a visually hidden live region intended only for committed announcements.

Its ownership should be narrow:

- no visual layout responsibility;
- no domain mutation;
- no observation of unrelated DOM changes.

### 4. Observe semantic state transitions, not text mutation

Trigger the announcement from the commit marker/event.

For DOM-based implementations, a narrowly configured observer might watch only a commit-state attribute rather than `characterData` or broad `childList` mutation.

Framework/event-driven code may call the announcer directly on semantic commit instead.

### 5. Announce exactly once per committed unit

On transition to committed:

```text
read final complete text
→ copy to live region
→ announce once
```

Settling/retirement should not produce a duplicate announcement unless it represents a new semantic message.

### 6. Keep visual timing and announcement timing separable

Reduced-motion may remove decorative animation while preserving the same semantic commit and announcement behavior.

If authored timing is semantically causal, define that separately; do not use accessibility implementation as the timing authority.

### 7. Tear down cleanly

Observers/listeners should detach when the owning surface/runtime is destroyed so stale DOM changes cannot generate announcements later.

## Why it works

It creates a semantic accessibility boundary: assistive technology receives complete meaningful units instead of the visual implementation's mutation frequency.

The announcement trigger is tied to content lifecycle, so changes to typing speed or rendering implementation do not automatically change semantic announcement behavior.

## Trade-offs

- requires an explicit commit signal;
- the live region may lag visual streaming until commit by design;
- complex multi-message concurrency needs ordering rules;
- screen-reader behavior varies, so browser/AT testing still matters;
- duplicating visible text into a hidden region requires care to avoid repeated announcements.

## Alternatives

Consider instead:

- render messages atomically for everyone;
- use framework/platform announcement APIs;
- `role=status`/`aria-live` on a low-frequency status region when updates are already bounded;
- announce throttled progress summaries for genuinely incremental progress;
- provide user controls to disable streaming and render final text immediately;
- use ordinary semantic document markup when the content is not transient status information.

## Failure modes

- live region contains the streaming text itself;
- observer watches every character/child mutation;
- final commit and later settle both announce the same line;
- non-target content is accidentally mirrored into the announcer;
- reduced-motion path skips the semantic commit entirely;
- announcer remains attached after teardown and announces stale content;
- hidden live region is visually hidden with techniques that also remove it from the accessibility tree.

## Verification

- streaming character/token mutations produce no repeated live announcements in the contract/test seam;
- one semantic commit produces exactly one complete announcement;
- settling/removal produces no duplicate;
- unrelated/non-target content is excluded;
- reduced-motion/atomic rendering produces the same semantic announcement count;
- observer/listener teardown stops later announcements;
- where an accepted claim requires observed assistive-technology behavior, obtain suitable evidence from the relevant browser/AT combination and an available capable observer; if independent acceptance is required, the observer is separate from the implementer. Human observation is not automatic. A source or DOM-only check does not prove what assistive technology announced.

## Related Core Principles

- `authority-mapping` — visual mutation is not the authority for semantic completion;
- `evidence-and-authority` — automated DOM assertions do not fully replace assistive-technology QA;
- `presentation-completion-barrier` — optional pattern when announcement completion participates in larger presentation scheduling;
- `exact-state-verification` — accessibility evidence applies to the tested candidate/browser/AT configuration.
