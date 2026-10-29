---
name: tracked-story
description: "Use when delivering a business story with traceability: analyze and get acceptance, implement, review, reconcile the README, then commit locally with authorization and a gate-backed evidence report."
---

# Tracked story

The SDLC policy (`policy/universal.md` in the repository) owns authority, commit and evidence rules; this skill orders the work and names the artifact each handoff produces. One story, or one independently deliverable subtask, per workflow. `copilot-sdlc` is the shared, host-neutral CLI despite its name; run it through `python scripts/sdlc.py` in this repository or by absolute path elsewhere.

Record each handoff as it closes. `commit-ready` refuses while a gate it needs is missing, so a gate recorded late is a claim without evidence.

1. **Analysis and acceptance** (`analysis`). Write the intent, acceptance criteria, assumptions, out-of-scope and risks into the story or an `analysis.md` beside it. Ask the user to accept them, then record the gate with that artifact and the approver. No implementation before acceptance unless the user explicitly accepts the risk of starting without it.

2. **Implementation** (`implementation`). Implement the narrowest change, run focused validation, then report what ran and what did not. Ask for commit authorization for this task. Record the gate with the validation evidence and the approver. Stage only reviewed files, then run `commit-ready` with an `ai commit: ` title; it writes the handoff report.

3. **Review** (`review`). Prefer a fresh reviewer session. Save findings, dispositions and residual risk under the story's `reviews/`, bounded to three rounds. Record the gate with that review file, then commit fixes with an `ai code review: ` title. If nothing actionable remains, record the verdict and stop.

4. **Customization** (`customization`). Required when the change touches `policy/`, `skills/`, `core/` or any `*-customization/` folder: name the layer that changed, run `python scripts/sync-customizations.py` and `python scripts/verify.py`, and record the gate with the drift-check result.

5. **Documentation** (`docs`). Reconcile the end-user README with current operation, architecture and limits, then record the gate with the README path. This closes the story before publication.

6. **Handoff.** Publication is the user's operation: never push. End with outcome, changes, evidence and limits, and use `DONE`, `BLOCKED_NEEDS_USER`, `FAILED`, `STUCK`, `LIMIT_REACHED` or `SECURITY_STOP` accurately.

```powershell
python scripts/sdlc.py gate --story SDLC-001 --gate analysis --artifact .sdlc/analysis.md --evidence "Criteria accepted in chat" --approved-by "<user>"
python scripts/sdlc.py commit-ready --workspace . --message "ai commit: <summary>" --prepared-by Codex --summary "<reviewed change>" --validation-summary "<checks run>" --co-author "Codex <noreply@openai.com>"
```
