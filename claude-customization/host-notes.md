## Claude host notes

- Permissions: configure workspace access through Claude settings; repository policy cannot override host permissions. The plugin's `PreToolUse` scope hook adds only what settings cannot: it denies writes outside the current project (or `SDLC_WORKSPACE_ROOT` when configured), commit titles without the required prefix, and staged credential files, and it denies `git push` (the user pushes). For everything else it defers to your settings.
- Commit through `copilot-sdlc commit-ready` and pass `--ai-name claude` (the title becomes `ai commit by claude: ...`) and `--co-author` with the attribution the harness specifies for commits (for example `Claude <noreply@anthropic.com>`). Keep any other trailer or session line the harness requires.
- Tracking hooks (`SessionStart`, `PostToolUse`, `PostToolUseFailure`, `Stop`) only record evidence, and only in a workspace that has an active story.
- Hooks and skills load at session start: restart the session after changing the plugin.
