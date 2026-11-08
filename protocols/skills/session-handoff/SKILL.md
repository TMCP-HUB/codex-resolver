# Session Handoff

## Purpose

Use this skill when ending a working session or when another session may continue the task later.

## Principle

A good handoff must let another agent continue without relying on hidden chat memory.

## Durable artifacts and manual presentation

Apply the universal channel-based presentation rule in `AGENTS.md`.

Durable machine artifacts retain their existing schemas and semantics. Persist required project artifacts in the authorized repository, Google Drive, or other declared system of record; retain exact assignment, candidate, result, and evidence references as applicable. Required durable readback and authority/independence gates still apply. Chat presentation is not authoritative state or proof of publication, dispatch, receipt, verification, or completion.

For a manual chat-to-chat handoff, assignment, or agent prompt, normally output exactly one flat, directly copyable plain-text block containing the complete manual message. Use plain-text labels in the suggested order below and include the required handoff content and exact durable references. Do not nest code fences, wrap the message as a file, or provide an attachment or download. Apply this to every receiving role, including a browser-based Control Director, Executor, or Verifier.

Exception: for every Owner-facing / LSO Director handoff of an approved workflow to a separate Workflow Director, output exactly two independently copyable text units, in this order: (1) the complete substantive workflow assignment with needed role, mode, objective, authority, scope and result destination; (2) the following fixed short launch instruction. The Owner pastes both into the same outgoing message; the host may convert the long paste to an automatically named attachment. Do not assume a filename or create a new gate.

```text
Ты Workflow Director. Прочитай приложенное к этому сообщению задание, включая автоматически созданный файл со вставленным текстом, и сразу приступай к исполнению по Project Resolver.
```

For an ordinary chat response, give a concise human-readable summary and relevant artifact references directly in chat. Never substitute a generated `.md` file or Markdown document attachment for the response.

`protocols/templates/HANDOFF.md` remains a repository template for durable handoff documents. Its Markdown file format does not dictate manual copy-paste presentation; carry the required content and references into the applicable manual output without changing the underlying artifact contracts.

## Reference-only workstream continuation

For a continuing approved workstream, carry one existing governing Issue/plan ref, final accepted target, completed PR/merge HEADs, active/remaining stages, current remote main, pending evidence/gates, blockers and next-action owner. Another Director reads current GitHub refs, not predecessor chat memory. Reuse compatible existing role sessions when appropriate; do not relay code, patches, base64 or large machine JSON through chat. HANDOFF supplies continuity, not new Owner approval, role authority or a background wakeup.

## Include in every handoff

- task goal
- current status
- what was changed
- files touched
- what was verified
- what remains
- known risks
- exact next recommended action

## Do not confuse with project history

A handoff is tactical and local to current work.
A chronicle is strategic and tracks the longer story of the project.

## Good handoff properties

- specific
- current
- short enough to scan
- complete enough to continue work safely

## Bad handoff examples

Avoid:

- continue from here
- almost done
- fixed the main issue
- just test it

## Suggested output order

1. Goal
2. Status
3. Changes made
4. Verification
5. Risks
6. Next step
