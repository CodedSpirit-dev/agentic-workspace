# Delivery modes

## Traditional

Use when phases have ordered gates, external approvals, or costly handoffs.
Store cycles under `phases/`. A phase must state entry criteria, planned
outcomes, exit evidence, open risks, and approval state. Do not open the next
phase merely because the calendar advanced.

## Sprint

Use for a maintained backlog delivered in timeboxed increments. Store cycles
under `sprints/`. A sprint states goal, dates, committed tasks, review evidence,
unfinished work, and retrospective actions. Move incomplete work explicitly;
never rewrite the completed sprint to make it appear finished.

## Flexible

Use for discovery, maintenance, research, or mixed work where a fixed sequence
would create fiction. Store cycles under `workstreams/`. Each workstream has a
bounded outcome, dependencies, checkpoints, and closure evidence. Flexible
means adaptable cadence, not missing scope or status.

## Changing mode

Record the reason as a decision, close or hand off the current cycle, update
the registry mode, and preserve old cycle folders. Stable artifact IDs do not
change.
