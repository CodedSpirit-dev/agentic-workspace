# Optional extensions

Extensions contain stack- or domain-specific guidance that is not part of the
portable core. Merely installing `agentic-workspace` does not activate their
rules. A destination must explicitly adopt the relevant guidance and, when an
extension provides a Spec Kit module, enable that module per project.

Available extensions:

- [`data/`](data/): optional column dictionary, metric catalog, migration, SQL,
  and glossary guidance;
- [`software/`](software/): evidence-based selection among FSD, Clean
  Architecture, Vertical Slice Architecture, Atomic Design, and a simple
  package-by-layer baseline.

A general declarative extension loader is planned but not yet implemented.
Adding an extension directory alone has no runtime effect.
