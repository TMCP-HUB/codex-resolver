# Research Engine Role Registry

The default Research Engine uses machine/agent roles plus one authority actor.

| Role | Actor type | Research labor | Authority note |
|---|---|---:|---|
| `OWNER_K0` | OWNER / K0 | no | project authority and adjudication only |
| `AI_R_LIAISON` | AI/system | yes | read-only interface; no mutation |
| `AI_R0_ARCH` | AI/system | yes | research foundation/control state |
| `AI_R_WHAT` | AI/system | yes | question/construct admission preparation |
| `AI_R_MASTER` | AI/system | yes | research execution |
| `AI_EVIDENCE_EXTRACTOR` | AI/system | yes | source-to-evidence extraction |
| `AI_SYNTHESIS_AGENT` | AI/system | yes | finding synthesis |
| `AI_R_VERIFIER` | AI/system | yes | automated independent verification; never repairs |
| `AI_R_REPAIR` | AI/system | yes | bounded repair only |
| `AI_ADVERSARIAL_VALIDATOR` | AI/system | yes | automated challenge/overclaim checks |
| `AI_RESEARCH_RELEASE_CONTROLLER` | AI/system | yes | research freeze/release preparation |

Research role identifiers above belong to the **Research Engine**; they do not create extra universal Liaison, Director, Software Auditor, Executor or Verifier types, and do not supersede their shared authority/independence contracts. A Research agent may serve different sequential Research phases only if the selected workflow admits this and any required independent research verification remains genuinely separate from the authoring/execution instance. This is not permission for human research labor or Research-to-Canon mutation.

No default role may be instantiated as an arbitrary external person. Generic `reviewer`, `expert reviewer`, `participant coordinator`, recruitment/survey operator, human coder/annotator/rater/validator, community solicitation liaison, or panel coordinator are invalid default Research Engine roles.

`OWNER_K0` is not evidence and is not a research sample. Owner/K0 may choose scope, priorities, transitions, acceptance/rejection/defer options, or other project decisions, but must not be assigned ordinary source collection, annotation, coding, participant activity, external consultation, or routine validation labor.

Work packages declare `EXECUTOR_ROLE` and `VERIFIER_ROLE`; the default schema restricts these to AI/system Research Engine roles and fixes the verifier as `AI_R_VERIFIER`.
