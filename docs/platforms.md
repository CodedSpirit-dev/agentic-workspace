# Platform and distribution support

`agentic-workspace` requires Python 3.11 or newer and has no runtime Python
dependencies. The supported command surfaces are:

| Context | Portable command |
|---|---|
| Installed product | `agentic-workspace` and `project-kit` |
| Product source checkout (POSIX) | `python3 bin/agentic-workspace.py` |
| Product source checkout (Windows) | `py -3.11 bin\agentic-workspace.py` |
| Destination repository (POSIX) | `python3 agentic-workspace/spec-kit/bin/project-kit.py` |
| Destination repository (Windows) | `py -3.11 agentic-workspace\spec-kit\bin\project-kit.py` |

Use an interpreter that resolves to Python 3.11 or newer. Do not assume the
ambiguous `python` command exists. The extensionless scripts in `bin/` use
Bash and are POSIX conveniences, not the portable API.

Git itself supplies the shell used for repository hooks on each platform.
Run `agentic-workspace check <repository>` after installation to detect an
adapter or hook that could not be connected in the local environment.

## Build release artifacts

Use an explicit timestamp to normalize wheel metadata and make release builds
repeatable:

```bash
SOURCE_DATE_EPOCH=1700000000 python3 -m build
```

PowerShell equivalent:

```powershell
$env:SOURCE_DATE_EPOCH = "1700000000"
py -3.11 -m build
```

Both wheel and source distribution must contain the complete payload and must
exclude `__pycache__`, bytecode, local build directories, Graphify output, and
Squad state. Some source-distribution backends encode container timestamps, so
the contract compares every member's path and content while requiring wheels
to be byte-identical. `tests/test_distribution.py` builds from two clean source
copies, installs the wheel into an isolated virtual environment, launches both
console commands, installs and checks a destination repository, exercises the
platform provider guard, and creates a project from installed resources.
