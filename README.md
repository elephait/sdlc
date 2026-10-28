# denistek

Personal engineering notes, prompts, reusable agent skills and an AI-native SDLC workflow that runs on VS Code Copilot, Claude and Codex.

| Path | What it is |
|---|---|
| `policy/` | Operating rules every host follows (`universal.md`, `research.md`) and `decisions.md`, the strategic decisions and pilot plan. |
| `core/` | Shared Python CLI, hook scripts, schema and tests. |
| `skills/` | Agent skills, one directory each, shared by all hosts. See [skills/README.md](skills/README.md). |
| `copilot-customization/` | Thin VS Code Copilot adapter: manifest, hook wiring, `host-notes.md`. |
| `claude-customization/` | Thin Claude adapter: plugin manifest, hook wiring, `CLAUDE.md`, `host-notes.md`. |
| `scripts/` | `sync-customizations.py` generates each host's plugin payload from the shared sources; `validate-skills.py` checks the skills. |
| `md/` | Notes and research. |

## One source, two hosts

Edit policy in `policy/`, skills in `skills/`, hook scripts in `core/scripts/`. Then run:

```powershell
python scripts/sync-customizations.py      # regenerate host payloads
python scripts/validate-skills.py          # check skills
python -m unittest discover -s core/tests
```

Only `host-notes.md` and the manifests differ between hosts. Files under `*-customization/plugin/{skills,scripts}` and `copilot-customization/plugin/com.github.copilot/rules` are generated; a unit test fails if they drift.

## Setup on a machine

1. Install the CLI once (it works from any workspace afterwards):

   ```powershell
   pip install --no-deps -e C:\dev\common\sdlc\core
   ```

2. Start tracking in a workspace. This repository was first tracked as story `COPILOT-CUSTOMIZATION-001` under another project, so give it a new story and drop the old local binding:

   ```powershell
   Remove-Item C:\dev\common\sdlc\.sdlc\active-story.json -ErrorAction SilentlyContinue
   copilot-sdlc project-onboard --workspace C:\dev\common\sdlc --story SDLC-001 --intent "<one-line intent>"
   ```

   For any other workspace use its own `--workspace`, `--repository`, `--story` and `--intent`.
3. Copilot: install `copilot-customization/plugin` in VS Code, then start a new session.
4. Claude: see [claude-customization/README.md](claude-customization/README.md). In short, load the plugin with `claude --plugin-dir C:\dev\common\sdlc\claude-customization\plugin`; this repository's root `CLAUDE.md` already imports the policy, and another project adds `@C:/dev/common/sdlc/claude-customization/CLAUDE.md` to its own `CLAUDE.md`.

### Troubleshooting

- `ERROR: Story X already belongs to <project> (<repository>).` A story ID is bound to one project and repository in the local database, and onboarding never rebinds it. Use a new `--story`, or pass the original `--project` and `--repository` if you really are continuing that story.
- `Workspace already has active story Y.` Delete `.sdlc\active-story.json` (local state, git-ignored) before onboarding a different story.
- Running the `pip install` twice is harmless; the second run just reinstalls.
