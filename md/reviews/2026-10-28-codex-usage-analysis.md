# Codex usage analysis

Question: did Codex underperform, or did it have more to do? Asked 2026-10-28 after a report of fast credit consumption.

## Verdict

The record cannot support either claim. There is **no Codex session in the evidence**: zero sessions, zero events, and no Codex commit. The only host-attributable artifacts are two commits, `3627ca2` (Copilot) and `5247c8c` (Claude, via its co-author trailer). Codex's adapter work is present in the working tree, staged and uncommitted, so its cost has no counterweight in the record.

"No measured output per unit of spend" is not the same as "worse". The honest answer is that the question was unanswerable before this change, and the fix is instrumentation, not a verdict.

## What the evidence contains

| Fact | Value |
|---|---|
| Stories | 3, all `DRAFT`: `COPILOT-CUSTOMIZATION-001`, `STORY-1234`, `SDLC-001` (intent "claude ready") |
| Sessions | 2, both `implementer`, both on `COPILOT-CUSTOMIZATION-001` |
| Session models | `copilot-model-unavailable`, and one null |
| Events | 16, of which 6 failed (37.5%); tool events 6, of which 2 failed |
| Host column | none, until this change |
| Token, credit or cost fields | none. Scorecard token fields are hardcoded `null` |
| Commits with a host trailer | Copilot 1, Claude 1, Codex 0 |
| High-resolution report | one, Copilot-only, 432 tool calls, 32 turns; that session is absent from the database |

Two scorecards compound the confusion. `COPILOT-CUSTOMIZATION-001` is scored three times, pooling both sessions, with wall-clock rising from 1 second to 65 minutes. `STORY-1234` is scored `passed` with zero tool calls and zero duration. Outcome labels are self-reported, and `runtimeVerified` is a free flag, so neither can stand as a per-host efficiency measure.

## Why credits cannot be attributed yet

Codex bills in credits; the tracker records events, not billing units. To answer the original question, the record needs, per session: a host label, the real model identifier, input/output/cache token counts, host billing units, a per-session (not story-level) scorecard, and turn or prompt counts. Non-hook hosts also need explicit evidence entry, because session `fa0cc9d7` recorded zero `PostToolUse` events: even its tool volume is invisible.

## What this change adds

- `sessions.host`, with an additive migration so existing databases and active stories are not rewritten.
- `session-start --host codex|claude|copilot|deepseek`, and `host` in the session summary of tracking reports.
- The gate workflow, which bounds rework rather than measuring it: analysis and acceptance before code, review before the closing commit, and a required customization gate for adapter changes.

Token counts remain `null` on purpose. No host here exposes authoritative usage, and inventing a number would be worse than the gap.

## How to settle it

Run the same task twice on the same repository, one host per session, recording `--host` and stopping each session with a real outcome. Compare requirement pass rate and human-confirmed defects first, then tokens and credits. A single Codex session cannot settle it; a paired run on one story can.

Until then, the defensible statement is: this repository has no measured Codex outcome, and the credit question needs instrumentation that now exists for attribution, but not yet for billing units.
