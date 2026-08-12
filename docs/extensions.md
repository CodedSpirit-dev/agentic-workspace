# Extension architecture

## Current behavior

The installed product has one provider-neutral core. Spec Kit 2.1 also knows
three optional data modules: `column-dictionary`, `metric-catalog`, and
`migration-control`. They are activated per project with `project-kit
add-module`; no profile enables them automatically. Optional data procedures
live under `agentic-workspace/extensions/data/`.

There is no general extension loader in version 0.1. Adding files below
`extensions/` alone does not register modules, skills, agents, validators, or
hooks. This limitation is explicit so documentation never promises behavior
the CLI does not implement.

## Proposed declarative contract

A future release may discover versioned extension manifests with a shape like:

```toml
schema_version = "1"
name = "backend-dotnet"
version = "0.1.0"
requires_core = ">=0.1,<1"

[provides]
skills = []
agents = []
templates = []
validators = []
hooks = []
```

This is a design target, not an accepted file format. Its implementation must
preserve these boundaries:

- core schemas and lifecycle gates remain domain-neutral;
- activation is explicit and recorded in project state;
- extension resources are namespaced and versioned;
- install, update, disable, and conflict behavior are deterministic;
- validation identifies which extension owns every extra rule;
- extensions cannot silently overwrite provider adapters or user files;
- a missing extension yields an actionable compatibility error, not partial
  validation.

Before stabilizing a manifest, test at least one backend, frontend, and data
extension against the same lifecycle and evidence model.
