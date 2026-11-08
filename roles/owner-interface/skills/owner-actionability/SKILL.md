---
name: owner-actionability
description: Determine whether the Owner must act now and project the exact next action without leaking internal routing or manufacturing an Owner gate.
---

# Owner Actionability

## Purpose

Use this skill when the Owner Interface / Liaison receives current control state, a role result, or a completed subrole return and must answer: "What does the human need to do now, if anything?"

## Goal

Produce an Owner-facing frontier with one unambiguous action owner and next step. Never manufacture Owner work when the system already owns an admitted next action.

Core law:

```text
NO OWNER-FACING FRONTIER WITHOUT AN ACTIONABLE NEXT STEP
```

## When to use

Use this skill:

- before every substantive Owner-facing control update;
- after an Executor, Verifier, compiler, or bounded subrole returns control;
- before deciding whether a genuine Owner gate should be presented;
- when an upstream result says work is "ready" but the project objective may still be open.

Do not use this skill to:

- select an execution surface on behalf of Control Director;
- decide whether an Owner-reserved action is authorized;
- create Canon truth or implementation authority;
- replace project completion or transition semantics.

## Inputs

Collect only the admitted current-state facts needed to establish:

- current status and whether the project objective remains open;
- next authorized transition, if one exists;
- next-action owner;
- whether an admitted system execution route exists;
- whether Owner/K0 authority is genuinely required;
- whether a bounded manual external operation is unavoidable;
- the exact execution location and expected return when human action is required.

Treat upstream control and executability decisions as authoritative. Do not re-run routing or invent capability state.

## Execution contract

**Required execution capabilities for mandatory steps:** none beyond model reasoning and reads of already-admitted control/result artifacts.

**Supported execution modes:**

| Mode | Required capabilities | Claim/evidence boundary |
|---|---|---|
| assignment-bound reasoning | supplied control/result artifacts | May classify Owner actionability from supplied authoritative state; may not prove unsupplied remote/runtime facts. |
| artifact-backed reasoning | readable durable control/result artifacts | Same semantic classification with durable refs available for evidence. |

**Conditional / optional capabilities:** artifact reads when the assignment supplies refs rather than inline state. No repository, shell, browser, deployment, or mutation capability is intrinsically required by this skill.

**Mandatory evidence path and equivalent fallbacks:** bind the projection to the exact current control/result refs or supplied state. There is no equivalent fallback for missing authority, route-admission, or next-transition facts; request bounded upstream clarification instead of guessing.

**Unsupported environment behavior:** if mandatory control facts cannot be read or were never supplied, return a bounded upstream-information requirement. Do not turn missing machine state into an Owner preference question.

Absence of SBC context does not itself create `BLOCKED_NO_ADMISSIBLE_SURFACE`. `ORDINARY_CHAT` remains a valid Liaison/runtime mode for work whose mandatory steps require only capabilities actually available there. Never invent SBC Browser, PAK, provider, browser, or dispatch capability to make a route admissible.

## Required outputs

Produce a concise Owner projection containing, conceptually:

- `current_status_plain_language`;
- `user_action_required`;
- `next_action_owner`;
- `next_action_plain_language`;
- `execution_location_plain_language` when an action occurs outside the conversation/control surface;
- `exact_user_steps` only when human action is required;
- `expected_user_return` only when a result/answer must come back;
- `system_action_after_user`, or the immediate system-owned next action when no user action is required;
- `reason_for_user_involvement` only when user involvement is real.

These are projection semantics, not a new durable schema or authority source.

## Human-control class versus actual automation

When the Owner asks whether a flow is manual, semi-automatic or automatic,
distinguish the selected existing HC4/HC3/HC2/HC1 authority policy from
the physical actions actually proven available. HC2 does not make a manual
handoff into a completed automatic dispatch, and HC1 never authorizes new
business or Canon decisions. Use the existing actionability classifications
below. State the exact human step only when needed; otherwise retain the
system-owned control baton. Do not invent a new mode schema, scheduler,
execution role or silent retry capability.

## Actionability classification

Classify the frontier into exactly one semantic class before writing Owner-facing prose:

| Class | User action | Next-action owner | Required behavior |
|---|---:|---|---|
| `NO_USER_ACTION_REQUIRED` | false | system/control | Explain status and the system-owned next step. Retain the baton. |
| `OWNER_DECISION_REQUIRED` | true | Owner/K0 | Invoke `owner-decision-surface`; present only the genuine Owner choice. |
| `MANUAL_EXTERNAL_OPERATION_REQUIRED` | true | Owner/manual operator | Give one precise external operation, where to do it, and the exact result to return. |
| `BLOCKED_NO_ADMISSIBLE_SURFACE` | false by default | control/system | State the capability blockage and keep routing/escalation system-owned unless a genuine bounded manual operation has already been established. |
| `SYSTEM_OWNED_NEXT_ACTION` | false | system/control | Continue/dispatch the admitted action; do not hand routing to Owner. |

`BLOCKED_NO_ADMISSIBLE_SURFACE` does not itself authorize asking the Owner to choose an internal execution surface or manual execution. Control owns topology resolution.

## Procedure

1. Bind to the exact current control/result state.
2. Determine whether the objective is complete or still open.
3. Determine the already-authorized next transition, if any, and consume the existing route/admissibility result rather than recomputing it.
4. If an admitted system route exists for an authorized next action, classify `SYSTEM_OWNED_NEXT_ACTION` or `NO_USER_ACTION_REQUIRED`; retain the baton and state what the system does next.
5. If a genuine Owner/K0 authority question is the blocker, classify `OWNER_DECISION_REQUIRED` and hand only that question to `owner-decision-surface`.
6. If no autonomous route exists and upstream control has established that a specific external human operation is truly required, classify `MANUAL_EXTERNAL_OPERATION_REQUIRED`; provide one bounded instruction, its location, and required return evidence.
7. If no admitted route exists but no specific human operation is established, classify `BLOCKED_NO_ADMISSIBLE_SURFACE`; report the system-owned escalation/routing state rather than inventing Owner work.
8. Emit the minimum plain-language projection needed for the Owner to understand status and, only when required, act.

### Post-verification continuation law

```text
VERIFICATION PASS != RETURN BATON TO OWNER
```

If the objective remains open, the next transition is already authorized, and an admitted system route exists, the Liaison must not stop at "ready to merge", "you can merge now", "state saved", a generic continuation question, or a request that Owner choose an execution surface. It reports/continues the system-owned transition. Promotion authorization and route admission remain owned by their existing control mechanisms, not by this skill.

### One completed PR does not finish an approved workstream

If the current approved outcome has further authorized stages, successful `EXECUTOR_RESULT`, `VERIFICATION_RESULT`, Assignment `COMPLETE` or merge is not a new Owner decision gate. Use the Director's durable Issue cursor to project the actual next system-owned step and retain the Director baton. Ask Owner only for a genuinely new reserved decision or unavoidable bounded manual operation; do not silently switch the controlling Director into Liaison or infer unfinished work from local files.

## Anti-patterns

Avoid:

- asking the Owner to choose among internal execution surfaces when Control can route;
- `Want me to continue?` when the objective remains open and no Owner input is required;
- presenting "ready to merge" as a manual Owner action when promotion is already authorized and admitted;
- converting missing machine information into an Owner choice;
- showing raw capability profiles, Director packets, schemas, or internal disposition vocabulary by default;
- presenting multiple internal-agent menus for a single manual operation;
- claiming `user_action_required = false` while giving the Owner an imperative action.

These guard `E-CONTROL-PLANE-LEAKAGE`, `E-USER-ACTIONABILITY-GAP`, `E-MACHINE-FORM-LEAKAGE`, and `E-LIAISON-AUTHORITY-ESCALATION` without creating a new global error ontology.

## Verification checklist

- [ ] Current status is understandable without internal topology knowledge.
- [ ] Exactly one next-action owner is identified.
- [ ] `user_action_required` agrees with the instruction actually given.
- [ ] An admitted system action is not converted into a human routing question.
- [ ] A genuine Owner gate is distinguished from a manual external operation.
- [ ] A route-admission blockage is not presented as Owner preference.
- [ ] Manual operation, when required, contains one exact action, location, and return result.
- [ ] The projection states what the system does after any required human input.
- [ ] No K0, Canon, Control Director, Executor, verification, or promotion authority is created by the Liaison.

## Minimal verdict format

- Actionability class
- Current status
- User action required: yes/no
- Next-action owner
- Exact next action
- Location, if external
- Expected Owner return, if any
- System action after return / immediate system action
- Evidence refs
