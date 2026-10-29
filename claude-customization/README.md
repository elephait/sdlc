# Claude customization

Claude adapter for the shared SDLC workflow. It contains only what is specific to Claude; policy, skills, hook scripts and the CLI are shared (see the [repository README](../README.md)).

| Path | What it is |
|---|---|
| `CLAUDE.md` | Always-on policy: `@`-imports the shared policy plus `host-notes.md`. No copy. |
| `host-notes.md` | The only Claude-specific instruction text. |
| `plugin/.claude-plugin/plugin.json`, `plugin/hooks/hooks.json` | Plugin manifest and hook wiring. |
| `plugin/skills/`, `plugin/scripts/` | **Generated** by `python scripts/sync-customizations.py`. Do not edit. |

## Use

1. Run the repository's `aicode.cmd` and select the project. It refreshes `.claude/CLAUDE.md` and `.claude/skills/` in that project from the latest shared sources.
2. Load the plugin from this checkout's `claude-customization/plugin` directory when plugin hooks are desired. Skills are also available project-locally after onboarding.
3. Optionally install the CLI once from this checkout's `core` directory so agents can call it from any workspace.
4. Start a new session in the selected project. Hooks record only where `.sdlc/active-story.json` exists.

## Limits

- Tracking records tool outcomes and session boundaries, not token usage.
- The scope hook fails open: if it crashes, Claude's normal permissions still apply. `commit-ready` re-checks commit policy itself.

For external research, read `policy/research.md` in the SDLC source checkout when needed. It is no longer imported into every session. The scope hook is a best-effort guard, not a shell parser or sandbox.
