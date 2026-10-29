# Codex setup and commands

Open `C:\dev\common\sdlc` as a project in the Codex app, then start a new chat there. Opening its parent `C:\dev\common` does not automatically load instructions or skills from the child repository.

The root `AGENTS.md` is generated from `policy/universal.md` and `policy/harness-notes.md`; DeepSeek reads the same payload. Research guidance is read on demand. Skills are generated into `.agents/skills/`; edit only `skills/`. No user-level settings, model selection or approval settings are installed.

## Runnable commands

One-command refresh and onboarding for SDLC itself, from any directory:

```powershell
C:\dev\common\sdlc\onboard.cmd --workspace C:\dev\common\sdlc
```

The explicit workspace selects SDLC even when another project was used most recently. Without it the launcher offers the project picker (or chooses the recent default without a terminal). It generates all four adapters, validates them, and refreshes tracking without changing the active story. It stops on failure and does not launch or stop agents. Plugin enablement in Copilot/Claude is still a one-time host setup. Use a new chat to load updated instructions when ready; the command does not restart a current chat.

If tracking is already running and you only want to refresh its registration:

```powershell
C:\dev\common\sdlc\onboard.cmd --workspace C:\dev\common\sdlc --skip-refresh
```

This skips adapter generation and validation. It preserves the current binding, session state, events, gates and installed workspace hooks. It may initialize missing database schema or update project-recency metadata, so it is not a read-only command. A conflicting `--story` fails rather than rebinding the project. The default full refresh also preserves tracking records, but can rewrite changed shared instruction/skill/hook files; defer that refresh until agents using those files are idle. No atomic live upgrade of a running host is promised.

Python 3.11+ is required. Run these in PowerShell from the repository:

```powershell
Set-Location C:\dev\common\sdlc
python scripts/sync-customizations.py
python scripts/verify.py
python scripts/sdlc.py --help
```

The CLI wrapper also works from any directory using its absolute path. Optional installation: `python -m pip install --no-deps -e C:\dev\common\sdlc\core` exposes both `sdlc` and the compatible `copilot-sdlc` command.

Tracking is optional for small tasks. Continue the existing active story; generate a fresh session ID for each Codex work session:

```powershell
$sdlcStory = (Get-Content .sdlc/active-story.json -Raw | ConvertFrom-Json).storyId
$sdlcSession = python scripts/sdlc.py session-start --story $sdlcStory --role implementation --host codex
python scripts/sdlc.py event --story $sdlcStory --session $sdlcSession --type validation --tool verify.py
python scripts/sdlc.py tracking-report --workspace C:\dev\common\sdlc
```

Record the validation event only after running the check; record its actual result in a decision or handoff report. `--progress` is valid only with `--type Iteration`, not a validation event. Use `event --failed --error-code ... --failure-message ...` for failures. Explicit records are not proof of automatic capture. The report exits 2 for missing or stale evidence.

When the current work is actually finished, close only the session you created:

```powershell
python scripts/sdlc.py session-stop --session $sdlcSession --outcome DONE
```

Do not close another agent's session or reuse a previously closed session ID. `DONE` requires actual acceptance evidence. For a workspace without an active binding, use `project-onboard` with its `--workspace`, `--repository`, a new `--story` and `--intent`; do not delete an existing binding to start this example.

## Handoff gates and local commit

The newer shared core requires recorded gates. Inspect them before a commit:

```powershell
python scripts/sdlc.py gate-status --story $sdlcStory
```

An implementation commit needs `analysis` and `implementation`; a review-fix commit needs `review` and `docs`. Changes to customization (including `scripts/` and the root launchers) also require `customization`. Record each gate only after its evidence and approval exist, using the actual approver rather than an assumed human approval, and pass `--recorded-by codex` so provenance is separate from approval. Stage the reviewed files before recording `implementation` or `customization`: they bind to the staged tree and to the current HEAD, so they must be re-recorded after any further staging or commit. `analysis` is story-level and stays valid. `gate --run-verify` runs `scripts/verify.py` and stores the exit code, test count and result; it refuses when the working tree has unstaged changes. For example (replace the placeholders):

```powershell
python scripts/sdlc.py gate --workspace C:\dev\common\sdlc --story $sdlcStory --gate review --artifact "<review-file>" --evidence "<checks and findings reviewed>" --approved-by "<actual approver>" --recorded-by codex
```

See [the tracked-story workflow](../skills/tracked-story/SKILL.md) for all gates. A gate record does not itself establish user authorization to commit.

After explicit local commit authorization, review and stage named files, then use the shared workflow (replace the summary, evidence and identity with actual values):

```powershell
python scripts/sdlc.py commit-ready --workspace C:\dev\common\sdlc --message "ai code review by codex: unify host customization" --ai-name codex --prepared-by Codex --summary "Describe the reviewed change" --validation-summary "Describe checks actually run" --co-author "Codex <noreply@openai.com>"
```

This command commits the current index and writes a handoff report. It does not run validation itself. Git signing settings remain effective. Publication remains a human operation.

## Use in another repository

Merge a short instruction into that project's existing `AGENTS.md`: “Read `C:/dev/common/sdlc/policy/universal.md` and `C:/dev/common/sdlc/policy/harness-notes.md`; read research.md only when researching external claims.” Preserve the project's own instructions. Copy the desired skill folders from `skills/` into that project's `.agents/skills/` (including metadata and references), and refresh them after source changes. Do not replace unrelated skills or instructions. Use the absolute CLI wrapper path and that project's `--workspace`, repository and story identity.

## Verify host activation

In a new chat rooted here, ask Codex to identify its repository instructions and list `$tracked-story` and `$distributed-service-design-review`. Invoke the latter on a small design question. Local checks verify generated content and Python behavior; they cannot certify discovery in an already-running app session.

Official references checked 2026-10-28: [AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [skill discovery and metadata](https://learn.chatgpt.com/docs/build-skills). The Codex adapter deliberately uses these repository mechanisms rather than assuming another host's plugin hooks are portable.
