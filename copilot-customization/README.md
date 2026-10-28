# Copilot Customization SDLC

Python 3.11+ tooling and an Agent Plugins 1.0 package for traceable
Copilot-assisted delivery. It coordinates stories, sessions, evidence,
reviews, local commits, scorecards, and retention while keeping business intent
in reviewable files.

## Run

No third-party runtime dependency is required. From the repository root:

```powershell
python -m copilot_customization.cli project-onboard
```

Onboarding creates or refreshes project tracking metadata and tracking-only
workspace hooks. Tracking runs at session start/end and after tools. Neither
the plugin nor onboarding installs a `PreToolUse` command hook, because running
a command before every tool can itself trigger repeated host permission prompts.
Ordinary work under `C:\dev` is pre-authorized. The agent must not request tool
permission for inspection, edits, validation, formatting, or local Git work.
If a permission dialog appears unexpectedly, the agent abandons that invocation
and immediately continues through a non-prompting local tool or equivalent
approach instead of relaying or repeating the dialog. Permission is appropriate
only for genuinely risky operations, external publication or exposure,
credential-file commits, access outside `C:\dev`, and current-task commit
readiness.

Inspect current evidence:

```powershell
python -m copilot_customization.cli tracking-report
```

The report places capture health and warnings first, returns exit code `2` when
the newest evidence is missing or older than 15 minutes, and detects hook
changes that require a new Copilot session. Use `--allow-stale` only when
historical output is intentionally acceptable. The report prioritizes sessions
needing review, keeps completed reviews compact, and collapses stale
retrospective evidence unless `--include-stale-analysis` is supplied.

For normal interactive work, use VS Code Copilot chat. After implementation and
static review, the agent asks one readiness question rather than stopping. To
authorize validation and a local commit, but not push, answer:

```text
ready to commit
```

The agent stages only intended files and invokes the deterministic
`commit-ready` backend. Direct CLI use is available for automation:

```powershell
python -m copilot_customization.cli commit-ready `
  --workspace $PWD `
  --message "describe the change" `
  --prepared-by "<identity>" `
  --summary "<delivery summary>" `
  --finding "<important finding>" `
  --validation-summary "<commit-specific validation evidence>"
```

Normal delivery commits use `ai commit: `; fresh-review fixes use
`ai code review: `.

## Architecture

| Component | Responsibility |
|---|---|
| `plugin/` | Portable skills, Copilot rules, lifecycle hooks, and permission policy |
| `src/copilot_customization/` | CLI, onboarding, coordination, reports, commit workflow |
| `sql/schema.sql` | SQLite coordination schema |
| `.sdlc/project.yaml` | Project identity, validation commands, and ledger location |
| Workspace `.sdlc/active-story.json` | Active story and ledger binding |
| Ledger `story.md` and JSON | Detailed intent, acceptance criteria, decisions, artifacts |
| SQLite | Cross-session events, failures, resolutions, reviews, and metrics |

Markdown and JSON are the human-reviewable source of intent. SQLite is the
local coordination index. Workspace and plugin hooks collect lifecycle and
outcome evidence without a pre-tool permission gate. The universal instructions
pre-authorize ordinary work under `C:\dev`; `commit-ready` directly invokes the
scope policy for credential, AI commit-title, and local commit enforcement.

## Delivery and handoff

1. Onboard the workspace and start a new session for tracking activation.
2. Keep detailed requirements and decisions in the tracked story.
3. Keep this README limited to operation, architecture, and limitations.
4. Implement and review statically; record validation as deferred.
5. Fix actionable review findings and statically re-review affected surfaces
   unless the user requested review-only output.
6. Ask one focused readiness question instead of stopping at the gate.
7. Do not generate, modify, or run unit tests before explicit current-task
   `ready to commit` approval.
8. At explicit current-task commit readiness, generate or update necessary unit
   tests, run relevant validation and the one-time formatter, then reconcile
   README, story, code, and evidence.
9. `commit-ready` creates one local commit and a ledger report named for the
   full commit hash.

The first commit analysis summarizes accumulated session evidence. Later
analyses include only additional findings and metrics since the preceding
analysis. Reports contain metric deltas, improvements, regressions, and a
content-hashed handoff snapshot for a fresh reviewer or LLM. Validation is
reported as `recorded` only when commit-specific evidence is supplied; it is
otherwise marked `notRecorded`.

Credential-like files are excluded from commits by default. An exception
requires explicit user approval recorded with approver, timestamp, optional
reason, paths, and staged Git blob hashes. Git push is always a separate
explicit-approval operation.

An editable virtual environment is optional:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --no-deps -e .
```

## Limitations

- Tracking hooks capture session lifecycle and post-tool outcomes. They do not
  intercept tools before execution.
- Standard Copilot surfaces do not expose authoritative token usage.
- SQLite coordinates processes on one shared filesystem, not across machines.
- Session analysis quality depends on recorded events and review summaries.
- Enterprise plugin distribution and managed enablement require administrator
  approval.
