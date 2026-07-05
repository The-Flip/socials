# Plans

This folder contains design documents for significant changes to `socials`.

Each document serves two purposes:

1. **Planning**: before implementation, describes the approach, trade-offs, and alternatives considered
2. **History**: after implementation, serves as a record of why things were built the way they were

Documents remain here whether the work is complete or not — they're valuable as architectural
decision records (ADRs) that future developers can reference to understand design choices.

## Format

Start each ADR with a `Status:` line (e.g. `Proposed`, `Accepted`, `Implemented in <PR/branch>`),
then:

- **Goal** — what we're trying to achieve
- **Background** — the user need or problem (link to [Product.md](Product.md) where relevant)
- **Approach** — the accepted design
- **Alternatives considered** — options weighed, with why they were rejected

Keep the "why" prominent — that's the part that's hard to reconstruct later.
