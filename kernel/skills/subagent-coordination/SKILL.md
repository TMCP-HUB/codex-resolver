---
name: subagent-coordination
description: Coordinate optional child agents within an admitted Executor assignment, using each actor's actual capabilities, authorized scope and available concurrency.
---

# Subagent Coordination

## Purpose
Optional **EXECUTOR** skill for completing one admitted Assignment with bounded child workers. "Coordinator" is an execution mode of the **same Executor**, not a new universal role, a Control Director, or an independent Verifier.

## Goal
Delegate bounded work when doing so improves delivery, join factual results, resolve in-scope integration issues, and produce **one** truthful final work product and `EXECUTOR_RESULT` with proportional context and resource use. Publish it when the assignment requires publication.

## When to use
- One or more bounded packages can be delegated usefully, including to a child with capabilities the coordinator lacks.
- Independent packages can benefit from supported parallel execution, or one Executor must integrate child results into one output.
- A proven native subagent facility exists and delegation is materially useful.

Do **not** manufacture extra roles or turn an executable Assignment into planning only.

## Inputs
Exact parent Assignment and acceptance, allowed source/repository scope, output locations, base/current state, any applicable budget or concurrency limits, required evidence, and actual execution surfaces. A child inherits only its explicitly delegated subset of this scope.

## Execution contract
**Mandatory for the coordinator:** read the parent task, retain its authority and scope, receive and integrate actual results, and produce the assigned output/evidence. In delegated mode, the coordinator needs actual spawn/join and integration capabilities; each child needs the capabilities for its own delegated actions. The coordinator does not need every child's tools merely because it coordinates them. In sequential mode, the coordinator needs the capabilities for every action it performs directly. If publication is required, the selected authorized publisher needs the actual write or publish capability for that destination, with evidence and readback as required by the assignment. For GitHub-backed remote publication, the selected publisher needs the actual GitHub branch, commit and remote-write operation; a local result or chat claim is not remote GitHub publication. Other Git destinations require only the operations and evidence actually specified for that destination, without assuming GitHub or a remote.

**Supported modes:**

| Mode | Required capability | Evidence |
| --- | --- | --- |
| Native children | Coordinator has actual runtime spawn/join and integration; each child has the source/tools for its own package | Real child results and observed completion; report actual concurrency |
| One Executor, sequential work packages | Required research/code/source capabilities directly in the Executor | Distinct factual work products; report `parallel=false` |
| GitHub-backed publication (when assigned) | Authorized GitHub branch, commit and remote-write operation through native Git or proven remote publisher | Fresh GitHub readback of repository, remote branch and full commit SHA by Control |
| Other Git destination (when assigned) | Actual authorized operation for the selected local or provider-hosted Git destination | Destination identity and evidence or readback required by the assignment; no implied GitHub, remote or push |
| Non-Git publication (when assigned) | Actual authorized write or publish operation on the selected destination | Destination identity and evidence or readback required by the assignment |

**Optional:** internet/search for public-source research, language/test runtime for implementation, GitHub APIs, native child isolation. Internet enabled in settings is not evidence a request actually succeeded.

**Fallback:** if native children are unavailable and parallel execution is *optional*, run the bounded work sequentially only when the Executor has the capabilities for those actions; do not simulate agents or claim parallelism. If mandatory parallelism or a required execution capability is unavailable, report the actual missing operation rather than silently changing the promise or requiring the parent to own tools used only by a capable child. Before dispatch, known missing mandatory capabilities are `ASSIGNMENT_NOT_ADMISSIBLE`; after a valid dispatch, genuine loss is `BLOCKED_RUNTIME_DRIFT`.

## Procedure
1. **Execute, don't re-plan the Assignment.** Read the provided MD/spec as the task. Freeze only the stated outcome, inputs, allowed scope, output files, and budget. Do not ask whether to start unless an actual authority or material ambiguity blocks work.
2. **Define useful work packages.** Give each child its objective, authorized scope, needed sources and outputs, and any applicable stop or resource limits. Select worker count and concurrency from the actual host facility, assignment, admitted budget and work; do not invent a universal cap. Nested delegation is available only when the actual host and parent assignment permit it and it serves the task. Avoid duplicate work and unnecessary agent trees.
3. **Spawn only if supported and worthwhile.** Use actual native child facilities, not assumed cross-product control. Coordinator retains parent `EXECUTOR` accountability. Children neither gain Director/Owner/Verifier authority nor merge or rewrite unrelated files.
4. **Collect and check once.** Obtain each child's actual output, source links, errors and limitations. Spot-check the evidence against parent acceptance. Never treat a child's assertion of completion as proof of publication or independent verification.
5. **Integrate.** Coordinator alone consolidates contradictions, removes duplicate claims and produces the final human-readable result. Do not let children push competing writes to the same file/branch. Any in-scope repair remains bounded by the parent Assignment; otherwise report the gap.
6. **Publish once if requested.** Publish the scoped output through the selected authorized destination and report its identity and evidence as required by the assignment. For GitHub-backed remote publication, use the admitted native Git or provider API route, report the exact repository, remote branch and full SHA, and do not merge; Control Director performs its own remote GitHub readback. No local checkout is implied by an authorized remote GitHub publisher. For another Git destination, perform only its assigned operations and provide the required destination identity and evidence; do not assume GitHub, a remote or a push.
7. **Return one result.** State work packages attempted/completed, real mode (concurrent/sequential), number of child workers actually spawned, final artifact references, focused checks, limitations, and `EXECUTOR_RESULT` to the specified Control recipient. Include the exact remote branch and full SHA for GitHub-backed remote publication; for other destinations include the identity and evidence actually required.

## Budget and stop conditions
Choose a decomposition proportional to the actual work, available capabilities and admitted limits. Keep child context task-specific; no repo-wide browsing, full test suite or duplicate research unless acceptance needs it. Do not launch replacements automatically after repeated failures; record `PARTIAL` with usable results. Stop on a real authority/scope conflict, exhausted admitted budget, the applicable same-boundary correction or tool-operation limit in `anti-loop-execution`, or mandatory capability loss. An external outage is a reported limitation, not a reason to design a new protection subsystem.

## Required outputs
One integrated output, child output refs (or explicit unavailable results), compact source/evidence list, actual parallelization status, selected publication destination identity when relevant, and one parent `EXECUTOR_RESULT`. Include final GitHub repository, remote branch and full SHA for GitHub-backed remote publication; use the actual destination identity and evidence for other assignments. Work-package results are not separate final Control decisions or V3 certificates.

## Anti-patterns
- Inventing a `COORDINATOR` universal role or permanent supervisor agent.
- Calling all internal reasoning "subagents" without actual spawned workers.
- Spawning unnecessary recursive workers, duplicating context or exceeding actual host, assignment or budget limits.
- Requiring planning deliverables before straightforward executable work.
- Mistaking an audit comment for a published code commit, or vice versa.
- Claiming that worker self-review is independent Verification; self-merging.
- Retrying an unavailable provider indefinitely or hiding a partial outcome.

## Verification checklist
- [ ] Parent authority, acceptance, tool access and budget are respected.
- [ ] Real child count/mode is stated; no fictional parallelism.
- [ ] Individual outputs are usable and source-linked where research requires it.
- [ ] Integration contains no unapproved scope or conflicting concurrent writes.
- [ ] Final output exists on the declared surface; GitHub-backed remote publication includes the exact remote branch and full SHA, and other destinations use their required identity and evidence.
- [ ] Parent `EXECUTOR_RESULT` is truthful and sent to Control, not self-promoted.
