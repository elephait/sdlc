# Python working rules

- Use the Python interpreter already selected for the workspace when it satisfies the project's declared version. Discover an existing interpreter before asking the user to select one, and do not create a virtual environment unless the project needs one.
- Respect `pyproject.toml` and existing environment, dependency, lint, type-check and test configuration. Do not install packages until a manifest change or a missing-dependency failure requires it.
- Prefer VS Code's Python and test integrations for diagnostics and focused tests. If discovery is unavailable, run the smallest equivalent command with the configured interpreter and state why the fallback is necessary.
- Keep imports, annotations and runtime behavior compatible with the project's supported Python range. Validate changed Python with focused diagnostics and tests before broadening the suite.
