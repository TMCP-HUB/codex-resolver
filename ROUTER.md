# Project Resolver Router

`ROUTER.md` chooses the smallest authoritative and executable work surface. It does not discover the entire repository.

## Workflow-bound entry

For an explicitly requested approved Workflow Director assignment, enter the existing `control-director` at its supplied frontier; do not restart Liaison or seek renewed approval. Read a designated current-message task attachment as specified in `AGENTS.md`, then apply the existing host, authority, compiler and destination-admission rules below. This entry introduces no new role or routing engine.

## Stage 1 host-to-role admissibility
Check the actual host **and agent instance** against `roles/MANIFEST.yaml` before activating a logical role. Codex Cloud may execute assigned Software work; the parent ChatGPT Work Director remains Liaison/Director/Verifier-only for its own controlled work and must not implement it. A **distinct Work-native Subagent** may be admitted as Executor, or as independent Verifier when separate from the candidate's Executor. Ordinary ChatGPT Chat may activate a shared role with the actual assignment, authority and capabilities. Director/Executor of one assignment and independent Verifier/Executor of one candidate cannot be the same instance. The Codex Cloud Executor skips Liaison bootstrap. No Work Subagent is admitted solely by a role label: actual native launch and available action/evidence paths still matter.

The `ORDINARY_CHAT` fallback for missing SBC transport data does **not** attest to the ChatGPT Chat product. Never use inferred model self-awareness or an untrusted role label as host provenance. When host identity is unknown, do not silently grant the ChatGPT Chat unrestricted profile. Stage 1 documents these boundaries but does not yet implement a trusted host-attestation runtime or cross-provider automation; do not claim mechanical enforcement.

## Binding provider and UI selection

For GitHub-backed Software, choose a **distinct admitted Executor through the actually selected native host**, including a Work-native Subagent or Codex Cloud. Both may publish into the existing GitHub candidate when authorized and capable. For a Work-native flow, using Work's own distinct Subagent is not a new transport, a new environment or a reason to request a fresh Owner decision. Preserve an explicitly frozen executor route while it is in flight; capability advertised by another tool is not permission to replace that running attempt.

**Not an admissible fallback for Executor dispatch:** Linear `@codex`/agent delegation, PR-comment `@codex address that feedback`, or a disconnected old Codex environment. Missing ACK, unpushed commit or failed publication means reconcile the original attempt and return exact WAIT/ESCALATE, not a silent new route. A different provider requires separate Owner-approved selection and admission.

A requested visible Desktop-integrated MCP browser cannot be replaced with hidden Chrome, background tabs or an unrelated Work cloud browser. GitHub reads need direct GitHub tools, not a browser.

## Cold start versus reuse of an agent instance

The selected **configured execution destination/transport** is not the same as a previously launched **agent instance**. For a first Assignment with no prior Executor and no in-flight dispatch, there is nothing to find or resume: after the existing authorized target/route admission, use the verified native launch operation to instantiate the Executor and record the actual resulting task/session identity. Do not require a pre-existing worker ID, issue a "no Executor found" STOP, open arbitrary historical tabs or repeatedly re-test unchanged transport setup. The normal first agent launch is not unauthorized infrastructure provisioning.

A currently running, assignment-bound Executor may be reused if compatible; never infer a worker exists because the transport is configured. A known dispatched task with unknown acknowledgement must be reconciled through its original native task identity and GitHub candidate before retry or replacement. If that attempt is confirmed terminal/absent and no recoverable unpublished code remains, a fresh Executor for the remaining authorized work is an ordinary new bounded dispatch, not a forbidden duplicate. GitHub-only absence is insufficient proof of a failed dispatch.

Optional child agents are an Executor execution technique, not a mandatory dependency for a Director to assign the first worker. Preserve provider/role/Owner/Canon authority, exact destination capability proof and the prohibition on legacy Linear dispatch. A genuine missing native launch action blocks only the dependent assignment, not unrelated admissible work.

## Routing contract

```text
KERNEL
→ select ENGINE by semantic capability and authority boundary
→ ENGINE selects a declared WORKFLOW
→ classify target authority/movability
→ classify execution-context fact authority
→ bind structured authorized claims and the exact supported execution envelope
→ compile structured assignment semantics under `contracts/ASSIGNMENT_COMPILATION_CONTRACT.md`
→ reject unauthorized identity/responsibility/evidence obligations
→ prove requested obligations are in the supported execution envelope
→ derive authorized mandatory actions + mandatory evidence gates from `COMPILED_ASSIGNMENT`
→ derive REQUIRED_CAPABILITIES only from compiled authority plus selected mandatory workflow/skill prerequisites
→ bind exact destination CAPABILITY_PROFILE
→ prove REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES
→ materialize ASSIGNMENT_ADMISSIBILITY
→ only if ADMISSIBLE: issue ASSIGNMENT
→ WORKFLOW activates a durable ROLE
→ ROLE loads only required SKILLS and referenced artifacts
```

Selection is based on the transformation and authority required, not filename similarity. Semantic engine capability is necessary but never sufficient for assignment.

Compilation is a mandatory upstream semantic gate. `REJECTED` compilation does not proceed to route, capability-profile selection, assignment admissibility, or executable assignment. The router consumes compiler output; it does not replace the deterministic compiler with prose judgment.

The universal executability contract is `contracts/EXECUTABILITY_CONTRACT.md`.

### Local workspace selection
Only when local-computer work is actually selected, route the actor to `kernel/skills/local-workspace-operation/SKILL.md`. Resolve and carry the configured per-user/device profile and applicable local rules before substantive local shell actions or project mutation, using the skill's permitted bootstrap modes. Preserve existing destination/capability ownership; a non-empty workspace-scope reference alone does not prove that the local policy was loaded or physically enforced.

### Tool choice after destination admission

Choose tools by the operation and required evidence, not by which connector happens to be connected. For GitHub-backed repository reads/writes, PR/Issue/review operations and CI observation, prefer the connected GitHub Connector or the Executor's authorized native Git/GitHub path. Remote Desktop Commander is a last-resort bridge for work that actually requires the user's computer (local files, installed runtime/CLI, application/device proof or otherwise unavailable deployment operations), **not** a default GitHub browser, terminal or repository client. Do not use it for routine GitHub work when a suitable direct route exists. Apply the provider-neutral native-first rule in `contracts/EXECUTABILITY_CONTRACT.md` to all roles.

**Same-provider tool substitution is not a transport fallback.** A missing `gh` executable or failed local shell command does not show that GitHub Connector/API is unavailable. Use the existing authorized GitHub tool for the same repository, action and claim when it is available; no new Owner decision, provider selection, execution environment, or remote CLI setup is needed. Previous successful Issue reads/writes prove only those operations and permissions. If all suitable methods for a mandatory operation fail, WAIT/ESCALATE the dependent step only, not the entire unrelated approved workstream. Keep prohibitions on legacy Executor dispatch and hidden-browser substitutions intact.

Reuse fresh exact-state evidence; avoid duplicate checks, screenshots, polling and repeated capability probes without a concrete unproven requirement or material state change. A missing direct operation requires bounded route reassessment, not an automatic desktop fallback. Keep existing authority, candidate publication and independent Verification requirements intact.

GitHub-backed Software tasks use the selected remote GitHub state, not arbitrary Owner-workstation clones, as their development baseline. Reuse an already configured target/environment; if an actually required repo-bound destination is unavailable, return the existing non-admissible/WAIT path and the smallest actionable setup need rather than provisioning a new environment. Dirty local leftovers in an unrelated workspace are not an admission blocker; preserve protected files and isolate any mandatory local work.

## Destination executability preflight

Before `ASSIGN`, the Control Director/router must compare the exact destination instance against every mandatory operation and evidence path required by the assignment, selected workflow, and selected mandatory skill steps.

Examples of concrete capability IDs include:

- `repository_remote_read`, `repository_remote_write`;
- `repository_local_checkout`, `git_local_worktree`, `shell`;
- `python_runtime`, `node_runtime`, `php_runtime`, `package_install`;
- `interactive_browser`, `playwright_runtime`;
- `database_access`, `deployment_access`, `outbound_network`;
- `ci_trigger`, `ci_read`, `connector:<name>`.

When mandatory capabilities truly remain unproven after reusing valid evidence, do not issue an executable assignment. Return:

```text
ASSIGNMENT_NOT_ADMISSIBLE
assignment_draft: <id>
destination: <destination_id>
required_capabilities: <set>
available_capabilities: <set>
missing_capabilities: <required - available>
mandatory_evidence_paths: <paths>
next: <select another already-authorized executable mode/destination | wait | escalate>
```

Do not intentionally route an impossible assignment to an Executor/Verifier merely so it can return `BLOCKED`. A later `BLOCKED_RUNTIME_DRIFT` remains valid when a capability disappears after a previously valid admissibility proof.

### Execution-mode substitution

A workflow/skill may expose multiple supported modes. The router may choose an alternate mode only when:

1. it remains within the same authority and semantic owner;
2. its declared capability prerequisites are satisfied by the destination;
3. it proves the same mandatory claims/evidence, or the assignment explicitly accepts a weaker claim;
4. the selected mode is recorded in `ASSIGNMENT_ADMISSIBILITY` and the assignment execution contract.

Remote repository state cannot silently substitute for local-worktree assertions. Playwright cannot silently substitute for a missing browser/runtime when Playwright itself requires checkout, Node/package execution, and browser binaries.

### Migration-preserved skills and patterns

An active skill/pattern migrated before the executability contract may not yet contain a dedicated execution-prerequisite section. Missing metadata means **UNKNOWN prerequisites, not zero prerequisites**. When such a legacy item is actually selected, inspect only that selected item's mandatory procedure/evidence steps and derive concrete required capabilities before assignment. If any mandatory prerequisite cannot be derived confidently, return `ASSIGNMENT_NOT_ADMISSIBLE` pending bounded clarification/annotation. Do not perform a repository-wide compatibility scan during ordinary routing.

## Foundation progressive disclosure

Foundation is an active engine only after Liaison cognitive intake has selected `ROUTE` because governed project formation is actually intended. Ordinary questions and useful in-chat reasoning may still terminate before any Engine is loaded.

For a Foundation route:

1. load `engines/foundation/MANIFEST.yaml`;
2. select the exact `form_project_foundation` workflow declared by the capability mapping;
3. load every item in `workflow_contracts.<workflow>.required_skills`;
4. load optional `engines/foundation/skills/design-discovery/SKILL.md` only when bounded exploration materially improves the seed, outcome, or consequential-unknown map;
5. bind the workflow's explicit roles and upstream provenance requirement;
6. feed all mandatory operations/evidence requirements into the normal compiler/capability/admissibility chain;
7. require the ordinary durable-output/reference/readback contract for all five declared Foundation outputs before readiness can be claimed.

There is no global skill discovery for Foundation. Do not recursively scan `engines/foundation/skills/` and do not load Canon merely because a raw idea is being formed.

Foundation artifacts are durable working state, not Owner/K0 authority and not Canon truth. The V0 Foundation workflow stops at `FOUNDATION_READY_FOR_OWNER_GATE`. When Canon formation is actually requested, its existing governed transition consumes the relevant available seed, outcome, unknowns, provenance and already-authorized decisions; use the existing Owner Foundation Gate only where applicable. Do not repeat an accepted decision or force full formation for an already-authorized bounded task.

## Canon progressive disclosure

Canon is an active engine only after `SYSTEM_MANIFEST.yaml` identifies `engine_id: canon` as `available`. For a Canon route:

1. load `engines/canon/MANIFEST.yaml`;
2. select the exact workflow named by the capability mapping;
3. load every item in `workflow_contracts.<workflow>.required_skills` plus only optional skills actually required by the assignment;
4. bind the workflow's explicit executing/consuming roles and upstream requirements;
5. feed those mandatory prerequisites into the normal compiler/capability/admissibility chain.

Do not reduce a multi-skill Canon workflow to one guessed skill. Do not recursively discover `engines/canon/skills/`. Engine availability does not confer Canon mutation authority.

When relevant Research feeds a Canon change, its authority chain is:

```text
RESEARCH
→ EVIDENCE / FINDINGS
→ CANON RECONCILIATION
→ explicit Canon authority where mutation is requested
→ ACCEPTED CANON
```

Research is undertaken only when needed for the actual outcome; absent that need, neither Research nor a fabricated reconciliation is a prerequisite for Canon. Relevant completed Research must be considered and reconciled through the existing boundary. Research findings, Software observations, and Verification results are not automatic Canon mutations; existing applicable Owner authority remains binding in either path.

## Research constitutional precedence

For every Research Engine route, apply this order before executing project-specific instructions:

```text
OWNER / K0 MACHINE-ONLY CONSTITUTIONAL DECISION
→ kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md
→ contracts/EXECUTABILITY_CONTRACT.md
→ engines/research/MANIFEST.yaml + RESEARCH_CONTROL_CONTRACT.md
→ project-specific research architecture
→ work package
→ method / freeze
→ executor prompt
```

If a weaker layer requests prohibited non-owner human research, reject that method with `REJECT_METHOD / REQUIRE_MACHINE_REDESIGN`. Do not route to humans and do not block the whole research project merely because direct human measurement is unavailable.

Research fields such as `MACHINE_EXECUTABLE=true` and `CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS=true` are method-level machine-only admission claims. They do not replace destination executability preflight. The destination must separately prove the capabilities required by `EXECUTION_SURFACE`, `SOURCE_ACCESS_METHOD`, `COMPUTATION_METHOD`, verification method, and mandatory validators.

`reconcile_research_chain` is read-only Research-domain control interpretation over exact already-durable Research artifacts. It does not itself execute Research or require a Research work-package admission artifact; any candidate next frontier must return to Control and pass the ordinary Research admission path before execution.

## Current routes

| Capability | Engine | Next surface |
|---|---|---|
| `form_project_foundation` | `foundation` | load Foundation manifest + `form_project_foundation` workflow + all required skills; load optional `design-discovery` only when selected; then generic executability preflight |
| `establish_canon_foundation` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + all declared required skills; then generic executability preflight |
| `register_canon_fact` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the fact-registration skill as the selected semantic operation |
| `register_canon_assumption` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the assumption-registration skill as the selected semantic operation |
| `register_unknown` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the unknown-registration skill as the selected semantic operation |
| `register_ambiguity` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the ambiguity-registration skill as the selected semantic operation |
| `register_contradiction` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the contradiction-registration skill as the selected semantic operation |
| `reconcile_research_into_canon` | `canon` | load Canon manifest + reconciliation workflow + all declared required skills; require exact Research/Canon refs and mutation authority for accepted changes |
| `classify_canon_change` | `canon` | load Canon manifest + production Canon-change workflow + all declared required skills |
| `validate_canon` | `canon` | load Canon manifest + validation-only `validate_canon` workflow + `validate-canon` skill; no freeze authority or freeze mutation is implied |
| `freeze_canon` | `canon` | load Canon manifest + validate/freeze workflow + all declared required skills and explicit freeze authority |
| `final_canon_reconciliation` | `canon` | load Canon manifest + final reconciliation workflow + all declared required skills and final Canon authority |
| `reopen_canon` | `canon` | load Canon manifest + reopen workflow + all declared required skills and explicit reopen authority |
| `implement_software_change` | `production/software` | load `engines/production/software/MANIFEST.yaml`, implementation workflow, then executability preflight |
| `diagnose_software_failure` | `production/software` | load Software manifest/diagnosis workflow, then executability preflight for required observations/tools |
| `plan_software_work` | `production/software` | load the Software Engine manifest and bounded planning skill set; require only the capabilities actually mandatory for planning/evidence |
| `review_software_change` | `production/software` | load the Software Engine review workflow; preflight the exact build/runtime/browser/repository evidence required; use Verification Engine only for independent claim verification |
| `verify_completion_claim` | `verification` | load `engines/verification/MANIFEST.yaml`; preflight every mandatory evidence path before assignment |
| `verify_exact_candidate_claims` | `verification` | load Verification Engine plus shared exact-state/evidence skills; distinguish remote-repository claims from local-worktree claims before assignment |
| `admit_research_question` | `research` | load the machine-only constitution, then Research manifest; method admission does not waive destination preflight for later execution |
| `plan_research_work` | `research` | validate machine-only method admission, then prove destination executability before activating an execution assignment |
| `execute_research_work` | `research` | run the declared machine-only research workflow only on an admissible destination/mode |
| `run_research_experiment` | `research` | use the default computational experiment/freeze contracts plus destination executability proof |
| `verify_research_work` | `research` | preflight automated Research validators and evidence access before assigning verification |
| `prepare_research_release` | `research` | freeze verified research and prepare the Canon reconciliation package without Canon mutation; preflight any mandatory validators/output surfaces |
| `reconcile_research_chain` | `research` | load the Research reconciliation workflow + required skill; resolve exact durable upstream Research refs; emit requirement-specific dependency state and candidate-only frontier without Research execution, direct dispatch, or Canon mutation |

## Non-materialized engine gate

If the required semantic capability belongs to another engine whose status is `not_materialized`, return:

```text
ENGINE_NOT_MATERIALIZED / OWNER_OR_SYSTEM_GATE
required_capability: <capability>
required_engine: <engine>
reason: <why this engine owns the task>
```

For example, `production/other-domains` remains unavailable until its own Engine is materialized. Do not simulate a missing engine by borrowing Software skills or inventing new authority.

## Role activation

After an engine is selected and destination admissibility is proven, use only workflows and roles declared by that engine manifest. Shared roles live under `roles/`; shared reasoning skills are loaded only when the workflow names them or the assignment requires their owned decision process.

The active instance is:

```text
Relevant State Slice
+ Engine
+ Workflow
+ Role
+ Destination Capability Profile
+ Assignment Admissibility Proof
+ Assignment
+ Required Skills
= Active Agent Instance
```

## Forbidden routing behavior

- no recursive repository-wide skill search during ordinary execution;
- no loading every skill "for context";
- no selection by fuzzy title similarity alone;
- no use of the archived legacy global skill index as a runtime router;
- no crossing engine authority boundaries because a nearby skill looks applicable;
- no treating missing legacy execution metadata as proof of zero prerequisites;
- no treating semantic engine capability as proof of destination runtime capability;
- no issuing an assignment with an unproven or non-empty missing capability set;
- no silently weakening a mandatory evidence claim because the destination lacks its execution surface;
- no silently continuing when required authority, evidence, engine capability, or destination execution capability is absent;
- **PROHIBITED:** default Research Engine transitions to participant recruitment, survey deployment, interviews, external human review, or any other new non-owner human research.
