---
name: tracked-story
description: "Use when: delivering a business story through clarification, implementation, fresh review, validation, commit readiness ('ready to commit'), and remote publication."
---

# Tracked Story

Follow `${PLUGIN_ROOT}/com.github.copilot/rules/universal.instructions.md`.

Use one story or independently deliverable subtask per tracked workflow.

1. Normalize intent, acceptance criteria, dependencies, assumptions, and open
   questions before implementation.
   Classify the work as a proof of concept or enterprise-governed change and
   apply the canonical policy's convention requirements accordingly.
2. Prefer separate sessions for intake, implementation, fresh review,
   corrections, validation, and publication.
   When automatic session creation is unavailable, create a compact handoff
   artifact with the story revision, accepted intent, decisions, constraints,
   and required validation.
3. Record sessions, tools, failures, resolutions, decisions, customization
   versions, models, and measurable outcomes with the `copilot-sdlc` CLI.
4. Review and correct statically until no actionable finding remains or the
   user accepts residual risk. Save the final verdict, fixes, residual risks,
   validation state, and further-customization decision under `reviews`. Do not
   generate, modify, or run unit tests, and do not invoke test-runner tools or
   commands. Unless the user requested review-only output, fix actionable
   findings and statically re-review the affected surfaces instead of stopping
   after reporting them.
5. At that point, if the user has not declared current-task commit readiness,
   ask exactly one focused question that explains readiness authorizes
   validation and a local commit but not push. Do not stop silently at the gate
   or ask repeatedly.
6. Only after the user explicitly gives current-task `ready to commit`
   approval, generate or update necessary unit tests, run the smallest relevant
   validation, and run the one-time formatter. Do not request another
   permission.
7. On explicit commit readiness, stage only the reviewed files and invoke
   `copilot-sdlc commit-ready` with the chat-derived summary and important
   findings. Before invocation, reconcile code and tests with the detailed user
   story, reduce the README to current high-level operation, architecture, and
   limitations, and resolve contradictory or stale statements. The backend
   creates one local commit and a content-hashed, commit-matched handoff report
   for a fresh reviewer. The first report summarizes all recorded evidence;
   later reports include only additional findings and metric deltas.
8. Use `ai commit: ` for normal delivery and `ai code review: ` for fresh-review
   fixes.
9. Treat remote publication as a separate approval gate.
