# Claude customization

Claude adapter for the shared SDLC workflow. It contains only what is specific to Claude; policy, skills, hook scripts and the CLI are shared (see the [repository README](../README.md)).

| Path | What it is |
|---|---|
| `CLAUDE.md` | Always-on policy: `@`-imports the shared policy plus `host-notes.md`. No copy. |
| `host-notes.md` | The only Claude-specific instruction text. |
| `plugin/.claude-plugin/plugin.json`, `plugin/hooks/hooks.json` | Plugin manifest and hook wiring. |
| `plugin/skills/`, `plugin/scripts/` | **Generated** by `python scripts/sync-customizations.py`. Do not edit. |

## Use

1. Load the plugin: `claude --plugin-dir C:\dev\common\sdlc\claude-customization\plugin` (or add it through your plugin settings). Skills are `/sdlc:tracked-story` and `/sdlc:distributed-service-design-review`.
2. Make the policy always-on. In this repository the root `CLAUDE.md` already does it. In another project add `@C:/dev/common/sdlc/claude-customization/CLAUDE.md` to its `CLAUDE.md` or your user `CLAUDE.md`; Claude asks once to approve an external import.
3. Install the CLI once so agents can call it from any workspace: `pip install --no-deps -e C:\dev\common\sdlc\core`.
4. Start tracking in a workspace: `copilot-sdlc project-onboard --workspace <path>`. Hooks record only where `.sdlc/active-story.json` exists.

## Limits

- Tracking records tool outcomes and session boundaries, not token usage.
- The scope hook fails open: if it crashes, Claude's normal permissions still apply. `commit-ready` re-checks commit policy itself.
