# Codex accumulated-commit review — 2026-10-30

Reviewed the cumulative changes after `74c2b39` through `ecedea3`, including
`01598ee`, `b0082d0`, `12b9642`, `9afba64`, `fbcaace`, `bb5404b`, and `ecedea3`.
The working tree was clean at review start. Scope: shared core, onboarding,
generated adapters, hook changes, tests, and Codex documentation.

## Findings and dispositions

1. **[P1] Workspace installation could delete user-owned skills.**
   `scripts/sync-customizations.py::_sync_skill_tree` treated a same-name skill
   directory as owned, overwrote its files and deleted everything outside the
   shared payload. A project's own `tracked-story` skill could therefore be
   destroyed during onboarding. Fixed: preflight all three host skill locations,
   refuse unmanaged collisions, track installed files in a manifest, and remove
   only previously managed obsolete files. Extra project files survive refresh.
   An older, unmarked installation is adopted only when its content matches.

2. **[P1] First-time single-project onboarding could not complete.**
   `scripts/onboard.py` invoked `project-onboard` without a repository, initial
   story or generic adoption intent. The new launcher's first-run/current-project
   path reached that command and failed for a fresh project. Fixed: share identity
   resolution with bulk onboarding, infer new-project defaults from Git and the
   directory, and supply an adoption intent. Existing identities and an explicitly
   supplied story or intent retain precedence. A real fresh-Git-project subprocess
   test exercises the complete launcher path with an isolated database.

3. **[P2] Bulk onboarding omitted project adapter installation.**
   `scripts/onboard-all.py` regenerated the SDLC checkout and registered projects,
   but never installed their instructions or skills. Menu option 2 / `--all`
   therefore reported readiness without activating project customizations. Fixed:
   install each project's adapters before registering it, report installation
   failure, and preserve dry-run and tracking-only behavior.

4. **[P2] Bulk refresh overrode existing project identity.**
   The changed bulk path refreshed previously tracked projects while explicitly
   passing the folder name and current origin. A logical project name differing
   from its checkout folder, or a changed origin, caused a configuration conflict.
   Fixed: prefer configured repository/story identity and let the core preserve
   the configured project name. A regression covers a differently named checkout.

5. **[P2] Verification could approve content outside the staged tree.**
   `core/src/copilot_customization/service.py::run_verify` checked unstaged
   changes only before execution and the index only afterwards. A verifier that
   edited a tracked file could return a passing result attached to an unchanged
   index. The verifier itself could also be untracked. Fixed: require the verifier
   in the index and reject HEAD or tracked-worktree changes during execution,
   alongside the existing index check. Regression tests cover both cases.

6. **[P2] Installed Codex instructions lacked a resolvable shared CLI path.**
   The copied harness notes referred to `scripts/sdlc.py`, host guides and shared
   policy relative to a project that did not contain the SDLC source. Fixed:
   include the absolute source checkout and CLI path in installed `AGENTS.md`,
   clarify relative SDLC references, and document refreshing after relocation.
   Tests inspect the generated project instructions; live host discovery remains
   unverified.

7. **[P2] Interactive onboarding discarded explicit options.**
   `scripts/aicode.py::interactive` passed empty argument lists to onboarding,
   losing `--db`, `--skip-refresh`, `--story` and `--intent` parsed by `main`.
   A tracking-only refresh could rewrite adapters and registrations could go to
   a different database. Fixed: forward options through menu actions, retain
   the selected database, and reject single-story options for bulk selection.
   A regression follows the explicit database/tracking-only path through `main`.

## Documentation and layers

The README's Strategic Goals now explicitly connect `aicode` with coding,
software design and AI-native practices and with project-specific improvement
from measured evidence. It describes baseline comparison, regression rollback,
human intent and missing metrics. Autonomous tuning remains a goal, not a claim
about the current implementation. Codex setup adds practical evidence-driven
improvement guidance without claiming automatic tool or token telemetry.

Changed layers: shared core, launcher/installer scripts, regression tests, Codex
host documentation and end-user README. Shared policy and skill source content
are unchanged; regeneration reports no adapter drift.

## Validation and limits

- Baseline: `python scripts/verify.py` passed all 96 tests, drift checking and
  skill validation with fixture directories confined to the authorized workspace.
- The initial default-temp run encountered Windows sandbox access errors; the
  elevated rerun was declined. Subsequent runs used `TEMP`, `TMP` and
  `SDLC_TEST_ROOT` under `C:/dev/common/.sdlc-test-work`, without elevation.
- An intermediate 102-test suite passed. Further onboarding regressions exposed
  two mocked subprocess outputs without stdout and a ledger-preservation fixture
  whose original ledger did not exist. The fixtures now supply stdout and create
  the ledger before asserting byte preservation. The focused 7 launcher tests
  and 9 bulk-onboarding tests then passed.
- Final `python scripts/verify.py`: **106 tests passed** in 105.088 seconds;
  adapter drift check passed and both skills validated with zero errors or
  warnings. `git diff --cached --check` also passed. Gates and the commit handoff
  retain this measured result; the suite was run directly, not through
  `gate --run-verify`.
- The explicit Codex review session was started during the review. Its records
  cover final validation and handoff, not total task elapsed time or token use.
- Verification uses the local working tree and index, not an isolated checkout;
  untracked dependencies, external services and changes reverted during a check
  are outside this freshness check's proof. No live Codex/Claude/Copilot activation,
  Linux runtime, or autonomous improvement loop was verified.

Disposition: all seven findings above have corresponding fixes and regression
coverage. Publication remains the user's operation.
