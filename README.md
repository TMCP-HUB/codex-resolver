<p align="center">
  <sub>AI AGENT ORCHESTRATION · GITHUB-FIRST DEVELOPMENT · INDEPENDENT VERIFICATION</sub>
</p>

<h1 align="center">PROJECT RESOLVER</h1>

<p align="center">
  <strong>Plan the work. Delegate to agents. Verify the result. Ship the outcome.</strong><br>
  Turn an approved project goal into a governed, multi-step workflow with GitHub Issues, PRs, specialized AI agents and evidence-backed delivery.
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#requirements-and-cost">Requirements &amp; cost</a> ·
  <a href="#how-it-works">Workflow</a> ·
  <a href="#engines">Engines</a> ·
  <a href="#project-status">Status</a> ·
  <a href="#license">License</a>
</p>

<p align="center">
  <a href="#project-status"><img alt="Status: Agent-native Stage 1" src="https://img.shields.io/badge/status-agent--native%20Stage%201-3366aa?style=flat-square"></a>
  <a href="LICENSE.md"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-7043a5?style=flat-square"></a>
  <a href="https://github.com/TMCP-HUB/codex-resolver"><img alt="Source: GitHub" src="https://img.shields.io/badge/source-GitHub-24292f?style=flat-square&logo=github"></a>
</p>

---

### AI agents can write code. Who keeps the whole project on course?

An agent can write a patch, run a command, or produce a convincing summary. That does not establish that it understood the owner's actual goal, respected earlier decisions, had permission to act, or proved the right outcome.

**Project Resolver** is a open-source, agent-native framework for **AI agent orchestration, project management, GitHub-first software delivery, and independent verification**. It connects **intent, authority, execution, and evidence** through durable contracts, reusable Agent Skills, and explicit role boundaries.

It **augments native model reasoning**, rather than replacing it with an endless checklist. Use it for ChatGPT Work, Codex, or another compatible AI agent with appropriate tools. Simple requests stay simple; governed workflows activate only when needed.

<table>
<tr>
<td width="33%" valign="top"><strong>◆ Intent before activity</strong><br><sub>Preserve the actual goal, accepted decisions, and authorized scope.</sub></td>
<td width="33%" valign="top"><strong>◆ Authority before action</strong><br><sub>Route to the right engine, role, and executable destination.</sub></td>
<td width="33%" valign="top"><strong>◆ Evidence before “done”</strong><br><sub>Separate the executor's claim from independently supported results.</sub></td>
</tr>
</table>

## How it works

```text
                     OWNER INTENT
                          |
                          v
                +-------------------+
                |      LIAISON      |
                | understand /      |
                | respond / route   |
                +---------+---------+
                          |
                    when routed
                          v
           +-----------------------------+
           | ENGINE -> WORKFLOW -> ROLE  |
           |           -> SKILLS         |
           |  authority + capabilities  |
           +--------------+--------------+
                          |
                          v
           +-----------------------------+
           |        EXECUTION            |
           |    artifacts + evidence     |
           +--------------+--------------+
                          |
                          v
           +-----------------------------+
           |  INDEPENDENT VERIFICATION   |
           |     + CONTROL / OWNER       |
           +-----------------------------+
```

<sub>Conceptual flow, not a claim of automatic dispatch. A Liaison can respond directly; execution and independent verification are used when the selected workflow and acceptance requirements call for them.</sub>

The rules underneath are intentionally explicit:

- **Owner intent is authority.** Existing approved decisions stay approved unless material new evidence changes the question.
- **Roles are durable; agents are replaceable.** An individual agent instance does not become the source of project truth.
- **Role mobility with boundaries.** A fresh Liaison can continue as an authorized Control Director in the same Chat; Work Director may delegate to distinct native Work Subagents or Codex Executors, and independent Verification stays a separate instance when required.
- **No assignment without executability.** Access to GitHub, a shell, a browser, CI, or another tool must be demonstrated for the selected destination, not assumed.
- **Artifacts are not evidence.** A report or green CI result does not, by itself, prove the approved business or architecture outcome.
- **Progressive disclosure.** Load the relevant engine, workflow, role, and skills rather than scanning the entire library.

## Quick start

Project Resolver is usable through the **existing [skills-only plugin package](plugins/project-resolver/)** or directly from this repository. The packaged Project Resolver plugin is provided as source files; a public Plugin Directory listing is not claimed. Other users can use the source files with a compatible agent.

### Option A — ChatGPT / Codex with the plugin

1. Use the available Project Resolver plugin (if it is installed and accessible to your account), or obtain the portable package in [`plugins/project-resolver/`](plugins/project-resolver/).
2. Connect the tools **actually needed by your work**: a project repository and GitHub Connector or native Git for GitHub-based development; an admitted coding agent for implementation; Preview or deployment integrations only when required.
3. Give the agent your project repository, existing Issue or approved goal, and the final result you want. The plugin's `setup` and `project-resolver` Skills load the **relevant** canonical Resolver contracts from the repository instead of duplicating the entire system.

> Installing the plugin does not grant GitHub write permissions, provide a Codex runtime, unlock a model, or automatically start background agents. Availability depends on the actual host and connected tools.

### Install a private ChatGPT plugin from this repository

If your ChatGPT account has access to **Plugin Creator**, you can install your own private Project Resolver plugin without waiting for a public Plugin Directory listing:

1. Download the current `main` ZIP from this public repository (Code → Download ZIP), or clone the repository.
2. Open `plugins/project-resolver/`. Package **the contents of this directory** as a ZIP, keeping `plugin.json`, `.codex-plugin/plugin.json`, and both `skills/*/SKILL.md` paths at the ZIP root. Do not package the entire Resolver repository as a plugin.
3. In ChatGPT Plugin Creator, create one private plugin from that ZIP. Connect GitHub and any other tools separately, as needed for the tasks you actually delegate.
4. On later changes, **update that same plugin** through Plugin Creator; do not create another plugin. Your Plugin Creator interface and account permissions determine whether this operation is available.

The plugin is a small, portable entry point. For GitHub-backed work it reads relevant, current Resolver guidance from [`TMCP-HUB/codex-resolver`](https://github.com/TMCP-HUB/codex-resolver), rather than copying all engines into the plugin. Installing this package does not grant access to private repositories, execution agents, or paid tools.

### Option B — Use any compatible AI agent directly

No ChatGPT subscription or plugin is inherently required to **read and apply** Project Resolver's open-source methodology.

1. Make [this repository](https://github.com/TMCP-HUB/codex-resolver) accessible to the agent through GitHub or a suitable file context.
2. Start at [`AGENTS.md`](AGENTS.md) for agent entry and [`BOOTSTRAP.md`](BOOTSTRAP.md) for fresh human-facing Liaison intake.
3. Load [`SYSTEM_MANIFEST.yaml`](SYSTEM_MANIFEST.yaml), [`ROUTER.md`](ROUTER.md), and only the selected workflow, role and Skills. The target project keeps its own accepted decisions and stronger restrictions.

A local clone is optional for a real local-runtime requirement, **not the default system of record**:

```bash
git clone https://github.com/TMCP-HUB/codex-resolver.git
cd codex-resolver
```

### Example: deliver a multi-PR result

```text
Use Project Resolver from https://github.com/TMCP-HUB/codex-resolver.
Target repository: OWNER/REPO
Governing work: existing Issue or Owner-approved objective.

Act as Control Director for the entire approved outcome, not a single PR.
Use existing configured tools and execution environments.
Break the approved result into only necessary bounded assignments.
Have separate Work Subagent or Codex Executors publish authorized GitHub branches and Draft PRs.
Use independent Verifiers for candidates whose gates require them.
Review exact PR HEAD, existing CI and applicable Preview evidence.
After authorized merge, read back main and continue remaining approved steps.
Do not ask me to reapprove decisions already made or create parallel systems.
Stop only when the final outcome is evidenced or a genuine blocker is reached.
```

**Governed promotion matters:** CI success alone is not permission to merge. Director merges only within previously granted authority and after required evidence and independent review. An active Work session can carry several stages; automatic restart after a session ends is **not** bundled.

### Retired coding transports are not fallback execution routes

For GitHub Software work assigned through a Work Director → distinct native
Work Subagent or Codex Executor → GitHub route, do not dispatch implementation
via retired Linear `@codex`, PR-comment `@codex address that feedback` or
detached legacy Codex environments. Use the selected admitted Executor and
its actual published PR HEAD.
When that route is unavailable, keep the existing attempt and report the
blocker instead of moving to a legacy transport.

When Owner chooses a **visible Desktop-integrated browser MCP**, hidden Chrome,
background tabs and a separate Work cloud browser are not equivalent.
GitHub Connector handles ordinary code/PR/CI operations without a browser.
Other manual or provider routes remain possible only when separately
authorized and admitted.

## Requirements and cost

The **core requirement** is an AI agent that can access the applicable Resolver instructions and the relevant project context. Actual write/verification operations also need the target tool permissions and appropriate execution environments. The framework is not limited to OpenAI or software projects.

For a **ChatGPT Work + GitHub** workflow, these are practical subscription examples, not mandatory product dependencies:

| Component | Practical starting setup | Optional high-throughput setup | Why you might use it |
| :-- | :-- | :-- | :-- |
| AI host | [ChatGPT Plus](https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus) — **$20/month** | [ChatGPT Pro 100](https://help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers) — **$100/month** | More room for lengthy Work/Codex agent workflows; actual model/tool availability and usage limits depend on the account |
| Source control | [GitHub Free](https://github.com/pricing) — **$0** | [GitHub Pro](https://docs.github.com/en/get-started/learning-about-github/githubs-plans) — **about $4/month** for individuals; [Team](https://github.com/pricing) **$4/user/month** for organizations | GitHub repos, Issues, PRs, CI and additional private-repository features |
| Preview / backend | Existing project environment or [Cloudflare Workers Free](https://developers.cloudflare.com/workers/platform/pricing/) — **$0** if suitable | [Cloudflare Workers Paid](https://developers.cloudflare.com/workers/platform/pricing/) — **from $5/month**, plus usage beyond included allowances | Only for projects actually using Cloudflare Workers/Pages or requiring its paid quotas |
| Remote computer bridge | Not required; [Desktop Commander Free](https://desktopcommander.app/pricing/) — **$0** if local access is truly necessary | [Desktop Commander Pro](https://desktopcommander.app/pricing/) — **$20/month** | Exceptional local files, device/CLI/runtime inspection or deployment unavailable through direct provider tools |

**Budget illustration (USD/month, before tax and metered overages):**

- **Practical ChatGPT/GitHub start:** approximately **$20** with Plus + GitHub Free and no paid deployment/desktop add-ons.
- **Optional power-user stack:** approximately **$129** = Pro 100 ($100) + GitHub Pro ($4) + Workers Paid minimum ($5) + Desktop Commander Pro ($20).
- **Alternatives:** Claude, Codex, other compatible agent clients and free or self-hosted execution surfaces may be used where their real capabilities satisfy the chosen workflow. Additional API usage, Codespaces, hosted services and provider overages are separate charges.

**Desktop Commander is not a default development tool.** For GitHub files, commits, reviews, Issues, PRs and CI, use a connected GitHub Connector/API or an Executor's authorized native Git. A remote computer bridge is a last resort for **genuinely machine-local** work, and a target repository may forbid it entirely. Do not create new environments or pay for subscriptions just because an agent sees them as available.

For a selected local computer, reuse the user's chosen workspace and instructions before substantive local shell actions or project writes, respecting any stricter rule that forbids shell bootstrap; see [Local Workspace Operation](kernel/skills/local-workspace-operation/SKILL.md). Remote-only tasks do not require local setup.

**Plan information:** estimates checked in November 2026. Pricing, limits and availability can change; always confirm the vendor checkout and capabilities of the account you will use. See [OpenAI Pro tiers](https://help.openai.com/en/articles/9793128-about-chatgpt-pro-tiers), [GitHub pricing](https://github.com/pricing), [Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/) and [Desktop Commander pricing](https://desktopcommander.app/pricing/).

## Engines

Five engine namespaces are **implemented in the current repository** with active manifests, workflows, and scoped skills, and registered as **available** in the [system manifest](SYSTEM_MANIFEST.yaml). This is code/documentation availability, **not** proof of live provider execution, a complete automated workflow, or Stage 1 end-to-end acceptance.

| Engine | Responsibility | Entry |
| :-- | :-- | :-- |
| **Foundation** | Turn owner material into an initial project foundation and topology, short of owner approval. | [Manifest](engines/foundation/MANIFEST.yaml) |
| **Canon** | Establish and reconcile governed project facts, assumptions, unknowns, and accepted state. | [Manifest](engines/canon/MANIFEST.yaml) |
| **Research** | Admit, execute, evaluate, and reconcile machine-only research work. | [Manifest](engines/research/MANIFEST.yaml) |
| **Production / Software** | Plan, implement, diagnose, review, and support scoped software changes. | [Manifest](engines/production/software/MANIFEST.yaml) |
| **Verification** | Independently test completion claims against the exact candidate, evidence, and acceptance target. | [Manifest](engines/verification/MANIFEST.yaml) |

<sub>Other production domains are not yet materialized. Actual execution depends on the required authority, evidence, and destination capabilities.</sub>

## Architecture at a glance

Project Resolver is a **modular monorepo**, not a monolithic system prompt.

| Layer | What's inside |
| :-- | :-- |
| **Entry & routing** | [`BOOTSTRAP.md`](BOOTSTRAP.md) · [`AGENTS.md`](AGENTS.md) · [`SYSTEM_MANIFEST.yaml`](SYSTEM_MANIFEST.yaml) · [`ROUTER.md`](ROUTER.md) |
| **Shared reasoning & authority** | [`kernel/`](kernel/) · [`contracts/`](contracts/) · [`protocols/`](protocols/) |
| **Agent composition** | [`roles/`](roles/) · [`schemas/`](schemas/) · [`library/`](library/) |
| **Task-specific capability** | [`engines/`](engines/) · [`adapters/`](adapters/) |

**GitHub refs, durable artifacts, and explicit decision records** are the evidence and state surfaces for repository-backed work. Chat history alone is not a canonical project record.

## Implemented control surfaces

The current `main` includes reference code and active contracts, not just proposed designs. These components are implemented in source; actual destination capabilities, authority and acceptance remain separate evidence claims.

| Component | Present implementation | Boundary |
| :-- | :-- | :-- |
| **Project formation and topology** | [Foundation Engine](engines/foundation/MANIFEST.yaml), [`project_topology.py`](tools/project_topology.py), [`project_topology_repository.py`](tools/project_topology_repository.py) | Non-Canon working foundation; actual fresh start and Owner Foundation Gate remain distinct. |
| **Assignment compilation and admission** | [`assignment_compiler.py`](tools/assignment_compiler.py), [`executability.py`](tools/executability.py), [`resolver_spawn.py`](tools/resolver_spawn.py) | Structured reference enforcement does not automatically correct every manual Director decision. |
| **GitHub delivery and transition** | [`github_candidate_handoff.py`](tools/github_candidate_handoff.py), [`resolver_transition.py`](tools/resolver_transition.py), [Director](roles/control-director/ROLE.md) / [Executor](roles/executor/ROLE.md) | Published candidate/readback exists; Director owns later CI/Preview observation, verification and promotion. |
| **Durable state and continuation** | [`durable_artifact_port.py`](tools/durable_artifact_port.py), [`durable_readback_enforcement.py`](tools/durable_readback_enforcement.py), [portable entry](adapters/agent-native/README.md) | A fresh instance of the same logical role reconstructed a bounded verification assignment and prior finding from durable GitHub state, issued its own verdict, and returned it to Control without its predecessor's chat (Issue #7). General automatic cross-session delivery or wakeup remains unproven. |
| **Research and reconciliation** | [Research Engine](engines/research/MANIFEST.yaml), [`research_policy.py`](tools/research_policy.py), [depth guidance](engines/research/skills/research-execution-depth/SKILL.md) | Machine-only methods/reconciler exist; real Research acceptance still open. |
| **Resource governance** | [`resource_admission.py`](tools/resource_admission.py), [`resource_forecast.py`](tools/resource_forecast.py), [`resource_ledger.py`](tools/resource_ledger.py) | RG-01–RG-04 core is materialized; provider integration is conditional and unproven. |

## Project status

Project Resolver is **implemented and actively usable through agent-native workflows**, with canonical source, contracts and skills in this repository. It is not a hosted agent execution service or a promise that every supported client can automatically launch/restart agents.

| Capability | Current status |
| :-- | :-- |
| **Five governed engines** | Foundation, Canon, Research, Software, and Verification manifests/skills implemented; each workflow still requires actual authority and evidence |
| **GitHub-first software delivery** | Assignment compilation, destination admission, Executor-owned branch/Draft PR publication, exact candidate readback and Director-controlled promotion implemented and demonstrated in bounded flows |
| **Continuous approved multi-PR delivery** | Director/Owner Actionability/Planning/Handoff guidance merged in PR #26: maintain the Owner-approved workstream across independently accepted steps |
| **Portable Project Resolver plugin** | Skills-only package in [`plugins/project-resolver/`](plugins/project-resolver/) merged in PR #27; the packaged source is available here; a public directory publication is not claimed |
| **Research and project formation** | Reference engines and methods implemented; broader real-world end-to-end acceptance is tracked separately |
| **Unattended scheduling or session restart** | Not bundled or proven as a universal Resolver capability; reuse the existing host's supported native actions and durable GitHub handoffs |

**One current roadmap:** Issue #12 (and owning Issues #1–#11). Dated audit snapshots and archived plans are provenance; use current GitHub main and the applicable accepted Owner/Canon decisions for live work. Recent merged examples: #57 direct Owner instructions for Canon, #59 current Canon carrier continuity, #61 verification planning for capable actors, #62 conditional Canon synchronization and cutover guidance, and #63 selected obligations in assignment compilation.

<details>
<summary><strong>For maintainers: migration and semantic boundaries</strong></summary>

The repository evolved from the **Codex Software Playbook**. Accepted software practices and solution patterns were moved into bounded namespaces; historic material remains available under [`archive/legacy-codex/`](archive/legacy-codex/).

The [architecture migration map](ARCHITECTURE_MIGRATION_MAP.md) and [Canon migration map](CANON_ENGINE_MIGRATION_MAP.md) are historical migration records, **not live routing authority**. The current [system manifest](SYSTEM_MANIFEST.yaml), [router](ROUTER.md), relevant contract, and approved Owner/Canon decisions govern active work.

A **Core Principle** is not a **Solution Pattern**. Patterns are optional techniques with assumptions and rejection conditions, not universal rules.

</details>

## Community

Have a use case, found a boundary that doesn't work, or want to improve an engine?

- [Open an issue](https://github.com/TMCP-HUB/codex-resolver/issues/new) to describe the need and expected outcome.
- [Explore existing issues](https://github.com/TMCP-HUB/codex-resolver/issues) to avoid parallel work.
- Propose changes through a pull request; acceptance into the authoritative system is a maintainer decision.

## License

Project Resolver is available under the [Apache License 2.0](LICENSE.md). You may use, modify, and distribute it, including for commercial purposes, subject to the license terms.

The license covers the repository's Project Resolver code, skills, workflows, instructions, contracts, protocols, schemas, and documentation, except materials identified as subject to other terms. Third-party materials retain their respective licenses and notices. The license does not grant general rights to Project Resolver names or logos; see [Trademark Policy](TRADEMARKS.md).

The community edition is free. Commercial implementation, integration, support, maintenance, and service agreements may be arranged separately through [TMCP Hub](https://github.com/TMCP-HUB). TMCP Hub and its services are separate products and are not licensed by this repository merely because they are mentioned here.

---

<p align="center">
  <strong>PROJECT RESOLVER</strong><br>
  <sub>Intent → authority → work → evidence.</sub><br>
  <sub>Published by <a href="https://github.com/TMCP-HUB">TMCP Hub</a> (TMC Movers LLC, North Carolina). Developed by <a href="https://mixx.pages.dev">SpillikinS</a>.</sub>
</p>
