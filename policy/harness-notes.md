## Repository-harness notes

- Repository instructions load from `AGENTS.md`; skills live in `.agents/skills/`. Start a new chat after instructions or skills change.
- This harness installs no lifecycle hooks. Record evidence with the shared CLI; there is no automatic tool capture and no token accounting, so claim neither.
- Use the harness's configured model, sandbox and approvals. Repository instructions grant no filesystem or network access, and user configuration is not changed to make a task pass.
- Run the shared CLI from the SDLC checkout, found through `SDLC_HOME` or the `.sdlc/sdlc-source.txt` locator in a managed project, and pass this project's `--workspace`. Onboard with `--tracking-hooks none`; pass the harness identity with `commit-ready --ai-name` (title) and `--co-author` (trailer).
- Setup and runnable commands live in the checkout's `codex-customization/codex.md` for Codex and `deepseek-customization/deepseek.md` for DeepSeek.
