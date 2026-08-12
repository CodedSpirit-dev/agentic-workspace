# Portable commands

Project Kit requires Python 3.11 or newer. From the destination repository
root, use the repository-local launcher for the host platform:

```text
# Linux and macOS
python3 agentic-workspace/spec-kit/bin/project-kit.py <command>

# Windows
py -3.11 agentic-workspace\spec-kit\bin\project-kit.py <command>
```

Do not assume the ambiguous `python` command exists. Linux and macOS users may
also use the POSIX convenience wrapper:

```text
agentic-workspace/spec-kit/bin/project-kit <command>
```

When the product's Python package is installed, `project-kit <command>` is an
equivalent global entry point. Prefer the repository-local launcher in CI so
the engine and templates come from the same installed workspace version.
