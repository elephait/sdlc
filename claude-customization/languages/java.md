# Java working rules

- Use the repository's Maven or Gradle wrapper when present. Do not replace it with a machine-wide build tool or change the configured JDK merely to make a command run.
- Derive the required JDK and framework versions from the build files, wrapper configuration and repository documentation before selecting or installing tooling.
- Respect existing build profiles, dependency management, formatting, static-analysis and test conventions. Install a JDK or build tool only when the required version is genuinely unavailable.
- Run the smallest affected compile or test target first, then broaden validation when the change or failure warrants it. Preserve source and target compatibility declared by the project.
