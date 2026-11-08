# Security Property Calibration

## Purpose

Use this skill before selecting or evaluating security controls when the requirement is phrased broadly as "protect this", "make it secure", "prevent copying", "lock it down", or another label that does not yet define the property being protected.

## Goal

Turn an imprecise security request into an explicit, testable security-property statement so controls are judged against the real asset, adversary, trust boundary, prohibited outcome, achievable guarantee, non-goals, and residual risk.

This skill is architecture-neutral. It does **not** prescribe encryption, authentication, browser hardening, DRM, zero-trust architecture, network topology, storage technology, or any provider.

## When to use

Use when:

- a security requirement is stated as a slogan rather than an observable property;
- proposed controls may deter ordinary users without establishing the claimed guarantee;
- the client, server, operator, provider, or another actor has materially different capabilities;
- protected data crosses a trust boundary;
- a design review needs to distinguish confidentiality, integrity, authorization, privacy, abuse resistance, availability, or another property;
- residual risk must be stated before implementation or release.

## Do not use when

Do not use this skill to:

- replace a full threat model for a complex/high-risk system;
- choose controls before the property statement is coherent;
- label a system "secure" without a scoped claim;
- demand impossible guarantees from a component that already receives the protected data;
- dismiss deterrence or exposure reduction merely because it is not confidentiality.

## Inputs

- asset or capability being protected;
- intended users and operators;
- relevant actors/adversaries and their realistic capabilities;
- system/trust boundaries;
- proposed or existing security claim;
- legal/product constraints where relevant;
- existing controls and known residual risk.

## Required outputs

Produce a security-property record:

| Field | Required statement |
|---|---|
| Asset / capability | What exactly is protected? |
| Adversary / capability | Against whom or what capability? |
| Trust boundary | Where does trusted control end? |
| Prohibited outcome | What must not happen? |
| Achievable guarantee | What can the chosen system honestly promise? |
| Explicit non-goals | What stronger/different property is not being claimed? |
| Residual risk | What remains possible after controls? |
| Evidence needed | What would demonstrate the guarantee on the exact system? |

Also record unresolved assumptions that could materially change the property.

## Procedure

### 1. Name the asset and action

Avoid "content security" or "account security" as the final unit.

Prefer scoped statements such as:

```text
unauthorized actors must not obtain unpublished document bytes from server storage
```

or:

```text
an authenticated user may view a result but may not mutate another user's authoritative state
```

### 2. Name actor capabilities

Separate ordinary use from stronger capabilities where relevant:

- unauthenticated network caller;
- authenticated but unauthorized caller;
- stale or modified client;
- user controlling their own browser/device;
- privileged operator;
- compromised dependency/provider;
- attacker with storage or infrastructure access.

Use only actors relevant to the actual claim. Do not invent a maximal adversary merely to make the requirement impossible.

### 3. Draw the trust boundary

Ask where the protected information/capability becomes available.

A component cannot honestly promise secrecy from an actor that legitimately receives the plaintext/bytes unless another enforceable boundary still exists.

Distinguish:

```text
not delivered
!=
delivered but hidden by UI
!=
delivered and access-controlled for mutation
```

### 4. State the prohibited outcome

Make the failure observable.

Examples:

- unauthorized read;
- unauthorized mutation;
- forgery accepted as authoritative;
- sensitive data disclosed to an unnecessary provider;
- one user's capability used for another scope;
- availability loss beyond an accepted threshold.

### 5. State the achievable guarantee

Use the strongest claim supported by the boundary, not the strongest wording desired.

Examples of legitimate distinctions:

- confidentiality vs exposure minimization;
- prevention vs deterrence;
- tamper detection vs tamper prevention;
- authentication vs authorization;
- privacy minimization vs anonymity;
- best-effort abuse reduction vs proof of impossibility.

### 6. Record non-goals and residual risk

Explicitly say what remains possible.

If a user-controlled client receives rendered data, copying through screenshots, memory inspection, custom clients, accessibility interfaces, or equivalent privileged mechanisms may remain possible. That does not make exposure-minimization controls useless; it changes the claim they are allowed to support.

### 7. Map controls to properties

For each proposed control, ask:

```text
which prohibited outcome does this control reduce?
against which actor capability?
what bypass remains?
what evidence would show it works?
```

Remove controls that exist only because they "look secure" unless they provide a separately accepted deterrence/operational value.

### 8. Bind evidence to the calibrated claim

Use `evidence-and-authority` to avoid overclaiming and `exact-state-verification` when implementation/config/environment can move.

A test of UI copy prevention does not prove server confidentiality. A valid signature test does not prove authorization. A penetration test on one deployment does not automatically prove another deployment.

## Decision rules

- Security claims are scoped properties, not adjectives.
- Actor capability is part of the property.
- A control cannot prove a property outside the boundary it actually enforces.
- Deterrence, minimization, detection, prevention, and recovery are different outcomes.
- Residual risk is part of an honest design, not evidence of design failure by itself.
- If the desired property is impossible under current assumptions, change the requirement, boundary, or architecture explicitly rather than inventing a guarantee.

## Anti-patterns

Avoid:

- "disable copy, therefore confidential";
- "encrypted at rest, therefore authorized";
- "hidden endpoint, therefore protected";
- treating client-side inconvenience as secrecy from a client that has the bytes;
- adding controls without naming the prohibited outcome;
- silently changing the adversary model after verification;
- calling residual risk "zero" without evidence appropriate to that claim.

## Verification checklist

- [ ] Asset/capability is explicit.
- [ ] Relevant adversary capabilities are explicit.
- [ ] Trust boundary is explicit.
- [ ] Prohibited outcome is observable.
- [ ] Achievable guarantee does not exceed the boundary.
- [ ] Non-goals and residual risk are stated.
- [ ] Every material control maps to a property.
- [ ] Evidence is scoped to the calibrated claim and exact state.

## Pair with

- `authority-mapping` for authorization/decision ownership and trusted writers;
- `evidence-and-authority` for claim/evidence discipline;
- `exact-state-verification` for deployment/config provenance;
- `irreversible-boundary-reasoning` when a security-sensitive action has a non-repeatable commit boundary;
- `operational-auditing` for repository/deployment security risk review.
