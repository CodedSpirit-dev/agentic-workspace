# Optional SQL exploration conventions

Adopt this document only when a repository or governed project explicitly
enables the data extension. Keep exploration queries in a project-local
`sql/` folder, created when the first query is worth preserving.

## File naming

Use `sql/NN-purpose.sql`: a two-digit prefix in execution or discovery order,
followed by a kebab-case purpose. The sequence is part of the evidence trail.

```text
sql/
├── 01-inspect-source-row-counts.sql
├── 02-returns-by-category.sql
└── 03-reconcile-approved-total.sql
```

## Header comment block

Every SQL file should identify its purpose and assumptions before the query:

```sql
-- Purpose: question this query answers
-- Grain: what one row represents
-- Date window: exact filter, if any
-- Joins/assumptions: non-obvious choices and exclusions
-- Source: system or database where it was run
-- Author/date: who ran it and when
```

The compatible template remains at
`spec-kit/templates/sql/00-example-exploration.sql.tmpl`.

## Interval convention

For adjacent time windows, consider the half-open interval `>= date_from AND
< date_to` so a boundary belongs to exactly one window. This is guidance for
time-windowed work, not a universal mandate. Whatever interval is selected
must be explicit in the query header and verification evidence.

## Database-specific syntax

Flag engine-specific syntax such as PostgreSQL functions, SQL Server `TOP`, or
MySQL date functions in the header. Do not imply portability that has not been
tested.
