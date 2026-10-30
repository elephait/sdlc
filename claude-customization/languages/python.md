# Python working rules

- Use the Python interpreter the project already configures (virtual environment, `.python-version`, tool configuration) when it satisfies the declared version. Discover an existing interpreter before asking the user, and do not create a virtual environment unless the project needs one.
- Respect `pyproject.toml` and existing environment, dependency, lint, type-check and test configuration. Do not install packages until a manifest change or a missing-dependency failure requires it.
- Run the project's own test, lint and type-check commands directly, starting with the smallest equivalent target. When the project defines none, say so and state the fallback you used.
- Keep imports, annotations and runtime behavior compatible with the project's supported Python range. Validate changed Python with focused checks and tests before broadening the suite.
