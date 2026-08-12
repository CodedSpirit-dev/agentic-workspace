# Legacy project migration

1. Preserve the existing project and inspect its IDs, decisions, status,
   deliverables, evidence, and generated files.
2. Run dry-run first:

```bash
agentic-workspace/spec-kit/bin/project-kit migrate <project> --dry-run
```

3. Review the report. Select or accept the default `flexible` mode; migration
   must not fabricate historical artifacts or completion evidence.
4. Apply only after review:

```bash
agentic-workspace/spec-kit/bin/project-kit migrate <project> --apply
```

5. Register existing artifacts with their real IDs or aliases, add explicit
   relations, fill the migration workstream, regenerate indexes, and run
   strict validation.

Migration preserves existing files and creates a registry backup/report. It
does not silently renumber or rewrite historical documents. A successful
`--apply` seeds every declared module file, regenerates derived views, and
finishes by running strict validation; it fails instead of reporting success
for an invalid migrated project.
