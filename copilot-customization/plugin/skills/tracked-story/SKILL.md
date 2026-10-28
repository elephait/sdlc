---
name: tracked-story
description: "Use when delivering a business story with traceability: clarify intent, implement, review fresh, reach commit readiness ('ready to commit'), then commit locally with an evidence report; tracking, ledger and scorecard work."
---

# Tracked story

Follow the SDLC policy for authority, readiness and commit rules; this skill only orders the work. One story, or one independently deliverable subtask, per tracked workflow. The `copilot-sdlc` CLI is the shared, host-neutral backend despite its name.

1. **Intake.** If the story is shallow or the user wants it deepened, refine it with `/better` in prompt-improvement mode (rewrite the story, do not execute it) before implementing; the user must invoke it. Normalize intent, acceptance criteria, dependencies, assumptions and open questions. Classify the work as proof of concept or enterprise-governed.
2. **Sessions.** Prefer separate sessions for intake, implementation, fresh review, corrections and publication. When a session cannot be created, write a compact handoff: story revision, accepted intent, decisions, constraints, required validation.
3. **Record** sessions, tools, failures, resolutions, decisions, customization versions, models and outcomes with the CLI.
4. **Review loop.** Review statically and fix until no actionable finding remains or the user accepts the residual risk. Save the verdict, fixes, residual risks, validation state and any customization follow-up under the story's `reviews`.
5. **Readiness gate.** Ask the single readiness question from the policy.
6. **Commit.** After explicit readiness, validate and format as the policy says, reconcile the README (current operation, architecture, limitations only) and the detailed story with the code, stage only reviewed files, then run `copilot-sdlc commit-ready` with a chat-derived summary, the important findings, a commit-specific `--validation-summary` when validation ran, and the host's co-author trailer in `--co-author`. The backend makes one local commit and a content-hashed handoff report: the first summarizes all recorded evidence, later ones only new findings and metric deltas.
7. **Publication** is the user's operation: never push; tell the user the commit is ready.
