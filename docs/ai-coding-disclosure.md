# AI Coding Disclosure

This project was developed with the assistance of AI coding tools (a
large-language-model coding agent) used for drafting code, generating
boilerplate and accelerating implementation.

However, the following were performed and reviewed by me (the human author):

- **Architecture design** — the layered separation (UI / API / AI intelligence /
  data & knowledge / external research) and the core principle that *the LLM
  never decides the final ranking* were my decisions.
- **Implementation decisions** — the LLM provider abstraction, the
  deterministic scoring formula and normalisation, the embedding/vector-store
  auto-fallback chain, the relational data model (avoiding a single JSON blob),
  and the FACT/INFERENCE/RECOMMENDATION explainability scheme.
- **Testing and validation** — the automated test suite (35 tests, including the
  end-to-end flow and the four surprise-record cases) was written, run and
  verified against real execution output, not mockups.
- **Final integration and review** — the full application was run (backend +
  dashboard), exercised against live inputs (including a brand-new industry and
  process), and the results inspected before sign-off.

No fabricated data, sources, benchmarks or screenshots were used: every claim in
this repository is backed by real, runnable code and real execution output.
