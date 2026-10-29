# Codex setup and commands

Open `C:\dev\common\sdlc` as a project in the Codex app, then start a new chat there. Opening its parent `C:\dev\common` does not automatically load instructions or skills from the child repository.

The root `AGENTS.md` is generated from `policy/universal.md` and `policy/harness-notes.md`; DeepSeek reads the same payload. Research guidance is read on demand. Skills are generated into `.agents/skills/`; edit only `skills/`. No user-level settings, model selection or approval settings are installed.

## Runnable commands

One-command refresh and onboarding for SDLC itself, from any directory:

```powershell
C:\dev\common\sdlc\onboard.cmd
```

It generates all four adapters, validates them, and refreshes tracking without changing the active story. It stops on failure and does not launch agents. Plugin enablement in Copilot/Claude is still a one-time host setup. Start a new chat after refreshing instructions.

Python 3.11+ is required. Run these in PowerShell from the repository:

```powershell
Set-Location C:\dev\common\sdlc
python scripts/sync-customizations.py
python scripts/verify.py
python scripts/sdlc.py --help
```

The CLI wrapper also works from any directory using its absolute path. Optional installation: `python -m pip install --no-deps -e C:\dev\common\sdlc\core` exposes both `sdlc` and the compatible `copilot-sdlc` command.

Tracking is optional for small tasks. For a new tracked story (choose an unused ID; preserve any existing active binding):

```powershell
python scripts/sdlc.py project-onboard --workspace C:\dev\common\sdlc --repository elephait/sdlc --story SDLC-002 --intent "Unify agent customization" --ledger-root C:\dev\common\sdlc\.sdlc\ledger --tracking-hooks none
python scripts/sdlc.py session-start --story SDLC-002 --role implementation --session-id codex-sdlc-002 --host codex
python scripts/sdlc.py event --story SDLC-002 --session codex-sdlc-002 --type validation --tool verify.py --progress
python scripts/sdlc.py session-stop --session codex-sdlc-002 --outcome DONE
python scripts/sdlc.py tracking-report --workspace C:\dev\common\sdlc
```

Record the actual validation result in a decision or the handoff report; the event above only marks progress. Use `event --failed --error-code ... --failure-message ...` for failures. The report returns exit code 2 when evidence is missing or stale; explicit records are not proof of automatic capture. `DONE` requires actual acceptance evidence.

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
