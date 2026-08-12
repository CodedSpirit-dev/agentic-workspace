# Data extension glossary

**Deviation registry** — the `metric-catalog.md` section that records an
approved departure from a canonical formula, including its reason and owner.

**Grain** — what one row of a dataset represents. An explicit grain makes
comparisons and reconciliation meaningful.

**Half-open interval** — a date range shaped as `>= from AND < to`, preventing
adjacent windows from overlapping at the boundary.

**Migration-control status** — the current lifecycle value for a governed
data object. Change it in the same unit of work that performs the transition,
never in anticipation of unexecuted work.
