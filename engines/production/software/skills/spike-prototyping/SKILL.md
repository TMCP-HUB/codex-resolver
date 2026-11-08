---
name: spike-prototyping
description: Resolve a concrete feasibility question with a bounded disposable experiment and claim-specific evidence.
---

# Spike Prototyping

## Purpose

Use this skill when an idea, architecture, integration, animation, UX pattern, or workflow is uncertain and should be validated before production implementation.

## Goal

Reduce expensive rewrites by testing the highest-risk assumption first.
A spike is disposable by default.

## When to use

Use this skill when:

- evaluating a new workflow or architecture
- testing a Cloudflare integration or deployment pattern
- comparing libraries or frameworks
- experimenting with UI transitions or interaction models
- validating a calculator, menu, or admin UX flow
- checking whether an external system can integrate cleanly
- the phrase "let's see if this even works" applies

Do not use this skill for production implementation or long-lived architecture docs.

## Inputs

The concrete uncertainty, accepted claim, constraints, authorized experiment surface and available evidence.

## Execution contract

- A reasoning or source-only spike needs only the supplied or authorized relevant material; it cannot prove unobserved execution.
- An experiment requiring execution needs the actual authorized runtime or provider surface. A live call or deployment is not implied. If necessary evidence is unavailable, report the affected result as unproven or partial.
- Independent acceptance, when required, uses a separate available capable observer; verification does not itself require new tests.

## Core rule

Spike code is disposable unless explicitly promoted.

Do not quietly turn a prototype into production infrastructure.

## Spike structure

Recommended structure:

```text
spikes/
  001-short-name/
    README.md
    experiment files
```

Each spike should answer one concrete question.

## Procedure

### 1. Define the question

Good:

```text
Can Cloudflare Pages and Worker share auth state cleanly?
```

Bad:

```text
Build the whole auth system.
```

### 2. Define success and failure

Write:

- what would validate the idea
- what would invalidate it
- what constraints matter

### 3. Choose the smallest experiment

Prefer:

- one endpoint
- one page
- one interaction
- one animation
- one integration path

Avoid:

- full routing systems
- full database schema
- large component trees
- production auth/security complexity unless the spike is about auth/security

### 4. Record evidence

Collect only evidence needed for the spike question: for example, source observations, logs, timings, payloads, screenshots, browser behavior or deployment results when relevant and authorized. A screenshot, build, browser, provider call or deployment is not a universal spike requirement. Source observations do not establish unobserved runtime behavior.

### 5. Write a verdict

Use one of:

- VALIDATED
- PARTIAL
- INVALIDATED

## Comparison spikes

When comparing two approaches:

```text
002a-library-a
002b-library-b
```

Compare:

- complexity
- deployability
- performance
- DX
- maintainability
- compatibility with current stack

## Promotion rule

Only promote spike code into production when:

- any architecture decision actually required by the promotion is accepted
- the code quality is reviewed
- the disposable assumptions are removed
- proper verification and review happen

Otherwise rewrite cleanly.

## Anti-patterns

Avoid:

- shipping spike code directly to production without review
- testing multiple unrelated ideas in one spike
- rewriting the existing app during a feasibility test
- hiding uncertainty behind confident language
- keeping spike folders forever without verdicts

## Required output

- Question tested
- Constraints
- Experiment summary
- Evidence
- Verdict
- Recommendation
- Promotion decision: discard / partial reuse / promote
