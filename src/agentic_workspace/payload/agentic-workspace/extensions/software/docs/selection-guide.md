# Architecture selection guide

## 1. Establish the decision boundary

State whether the decision covers a frontend, backend/service, shared library,
design system, whole deployable, or only one module. A hybrid recommendation
must assign exactly one responsibility and boundary to each method. When a
product spans repositories or deployables with different change axes, evaluate
them as separate decision boundaries and name an owner for each.

## 2. Gather spec evidence

Read requirements and specs before the current folder tree. Capture:

- business capabilities and their expected change frequency;
- domain-rule complexity and required independence from infrastructure;
- command, query, workflow, and transactional boundaries;
- reusable UI and design-system requirements;
- team size, parallel ownership, refactoring experience, and onboarding needs;
- external systems likely to change;
- release units, monorepo/package boundaries, and supported platforms;
- current coupling, build/test constraints, and acceptable migration budget.

Unknowns remain `(TODO: confirm)` and lower confidence; they are not silently
scored as favorable.

## 3. Score candidates consistently

Use 0–3 for each applicable criterion: `0` conflicts, `1` weak, `2` viable,
`3` strong, and `N/A` when the criterion is outside the decision boundary.
Weights default to equal. Change a weight only when a cited requirement or
constraint justifies it.

| Criterion | Evidence question |
|---|---|
| Scope fit | Was the method designed to govern this software surface? |
| Change alignment | Does its unit match how requirements arrive and change? |
| Dependency protection | Does it isolate the policies or details that specs say will vary? |
| Independent delivery | Can teams change and verify bounded capabilities without broad edits? |
| UI-system fit | Does it support the required reuse and real-content testing? |
| Team operability | Can the team name, review, enforce, and refactor its boundaries? |
| Incremental adoption | Can it be introduced without an unjustified rewrite? |
| Verification | Can import rules, boundaries, and representative changes be tested? |

Scores inform discussion; they do not replace constraints. Do not turn `N/A`
into zero or compare aggregate scores across different software surfaces. A
high total cannot override an explicit incompatibility such as choosing FSD as
the sole backend architecture or Atomic Design as a persistence architecture.

## 4. Define the recommendation

Record:

- primary method per decision boundary and bounded companions;
- owned directories/modules/slices and allowed dependency direction;
- public APIs and an evidence-based trigger for extracting shared code; if the
  repository history is insufficient, leave the trigger `(TODO: confirm)`;
- one representative feature or use case mapped to the proposal;
- staged adoption, repository/deployable owners, preservation rules, migration
  budget, and stop point;
- alternatives rejected with evidence rather than generic pros/cons;
- risks and signals that reopen the decision.

Keep the incumbent design when it meets the specs and its measured friction is
below the migration cost.

## 5. Prove and trace it

Choose checks appropriate to the repository: import-boundary linting, dependency
graph rules, architecture tests, package visibility, circular-dependency checks,
public-API checks, component stories with representative content, or a small
change exercise showing affected files.

Create a `DEC-*` derived from or addressing the relevant `REQ-*`/`SPC-*`.
Create `CONV-*` for enforceable rules, `RSK-*` for material uncertainty, and
`VER-*` for observable checks. A diagram or folder example is explanatory
evidence, not proof that runtime boundaries hold.

The assessment frontmatter is the machine-readable contract:

- `draft` permits incomplete evidence and empty ID lists;
- `proposed` requires listed requirement/spec sources, draft decision IDs, and a
  `DEC-* derived_from REQ-*|SPC-*` relation for every decision;
- `accepted` additionally requires accepted decisions, active conventions, an
  active or passed verification, and relations connecting every listed
  companion to the declared decision graph.

Keep optional risk IDs empty when there is no material uncertainty. Never place
placeholder IDs in these lists; `project-kit validate` resolves every entry.

Review the decision on a dated milestone or when a stated trigger occurs, such
as growing cross-slice imports, repeated changes across unrelated technical
folders, framework types entering domain policy, design-system divergence, or
migration work exceeding its budget.
