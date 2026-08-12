# Software architecture methods

Use these as candidates, not presets. Folder names alone do not prove that a
method is implemented.

## Comparison

| Method | Primary unit | Governs | Core dependency rule | Best fit signal | Main cost |
|---|---|---|---|---|---|
| Feature-Sliced Design (FSD) | business slice within standardized frontend layers | frontend application structure and flow | a slice imports only from strictly lower layers; same-layer slices stay isolated except the bounded entity `@x` escape hatch | business-rich frontend whose features and pages change independently | taxonomy and import discipline |
| Clean Architecture | policies/use cases inside mechanisms and adapters | dependency direction around durable business rules | source dependencies point inward; inner policy does not name outer details | complex rules must remain testable and independent of UI, database, frameworks, or services | boundaries, mapping, and abstractions can be overbuilt |
| Vertical Slice Architecture (VSA) | request or use case end to end | application/service change boundaries | maximize cohesion inside a slice and minimize coupling between slices | work arrives as independently changing commands, queries, or use cases | duplication and local choices require refactoring skill |
| Atomic Design | atom → molecule → organism → template → page | UI design-system composition | compose and test parts and wholes concurrently | reusable UI language and resilient component system are primary needs | taxonomy can become ceremony or be confused with app architecture |
| Package by technical layer | component/service/controller/repository or similar technical role | simple code placement | team-defined; dependencies are often conventional rather than intrinsically enforced | small, stable, low-complexity system where a familiar layout is enough | a feature change spreads across folders as the system grows |

## Feature-Sliced Design

FSD is an architectural methodology for frontend applications. Its current
active layers are `app`, `pages`, `widgets`, `features`, `entities`, and
`shared`; the documented `processes` layer is deprecated. Not every project
needs every layer. `app` and `shared` are special cases without business
slices; other layers partition first by domain slice and then by purpose
segments such as `ui`, `api`, `model`, `lib`, or `config`.

The important rules are semantic:

- code may import slices only from layers strictly below;
- slices on the same layer remain independent and highly cohesive; keep the
  documented `@x` cross-import exception minimal and only on `entities` where
  a real entity relationship makes isolation unreasonable;
- each slice exposes a deliberate public API instead of allowing arbitrary
  deep imports;
- adoption can be incremental, and an architecture that is working should not
  be replaced without a demonstrated problem.

Use FSD for an application frontend, especially when navigation by business
area and controlled reuse matter. Do not choose it merely because the project
uses React, and do not use it as the default architecture for a library or a
backend service.

## Clean Architecture

Clean Architecture protects higher-level policies from delivery mechanisms.
Entities contain general business rules, use cases contain application rules,
interface adapters translate formats, and frameworks/drivers remain details.
The number and names of circles are illustrative; the non-negotiable property
is that source dependencies point inward. Boundary data stays simple and must
not leak database or framework representations into inner policy.

Use it when business rules are substantial and long-lived, external details
are volatile, or independent testing is a requirement. Avoid mechanically
creating a controller-service-repository chain for every operation. Clean
Architecture is not synonymous with a classic folder-by-type tree; it can be
implemented inside modules or selected vertical slices.

## Vertical Slice Architecture

VSA organizes an application around distinct requests or use cases and groups
the concerns needed to fulfill each one. Its design goal is high coupling
within a slice along the axis of change and low coupling between slices. Each
slice may use the simplest suitable domain-logic pattern and evolve when code
smells justify it.

Use it for services or applications where commands, queries, and business
capabilities change independently. The team must be able to detect duplication,
extract shared policy deliberately, and refactor local logic before it decays.
VSA and FSD are related by vertical organization, but they are not identical:
FSD defines a specific frontend layer/slice/segment model, while VSA centers on
end-to-end application requests and leaves internal organization open.

## Atomic Design

Atomic Design is a mental model for constructing UI systems through atoms,
molecules, organisms, templates, and pages. The stages work concurrently: real
content and full pages must test and influence the smaller components. The
method is technology-independent and concerns user interfaces, not JavaScript,
CSS, API, persistence, or application dependency architecture.

Use it as a companion when a design system, shared vocabulary, and component
resilience are important. With FSD, apply Atomic Design inside relevant `ui`
segments or a bounded shared UI kit; do not create a competing application-wide
folder hierarchy.

## Package by technical layer

`components/`, `services/`, `hooks/`, `controllers/`, and `repositories/` are a
common organization by technical role, not one formal methodology with a
canonical specification. It can be the lowest-cost honest choice for a small
or stable system. If selected, the decision must define allowed dependencies,
public entry points, ownership, and graduation triggers such as frequent
multi-folder changes, circular imports, an overloaded shared folder, or teams
blocking one another.

## Compatible combinations

- **FSD + Atomic Design:** FSD owns frontend application boundaries; Atomic
  Design owns composition inside selected UI segments.
- **FSD frontend + VSA service:** each side owns its repository or deployable
  boundary; API contracts connect them.
- **VSA + Clean boundaries:** VSA owns use-case placement; complex slices use
  inward dependencies for durable policy. Do not force identical layers into
  every simple slice.
- **FSD + Clean principles:** FSD owns the frontend map; framework-independent
  domain policy may use inward dependencies inside a bounded entity or module.
- **Package-by-layer with exit criteria:** retain a simple incumbent layout and
  migrate only the areas whose measured coupling crosses a recorded threshold.

## Primary sources

Consulted 2026-08-12:

- Feature-Sliced Design, [Overview](https://feature-sliced.design/docs/get-started/overview),
  [Layers](https://feature-sliced.design/docs/reference/layers),
  [Slices and segments](https://feature-sliced.design/docs/reference/slices-segments),
  and [Public API](https://feature-sliced.design/docs/reference/public-api).
- Robert C. Martin, [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html),
  2012.
- Brad Frost, [Atomic Design Methodology](https://atomicdesign.bradfrost.com/chapter-2/),
  2016.
- Jimmy Bogard, [Vertical Slice Architecture](https://www.jimmybogard.com/vertical-slice-architecture/),
  2018.

Package-by-technical-layer is intentionally labeled a local baseline because
there is no single canonical specification for it.
