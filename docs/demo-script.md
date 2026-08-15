# Demo Script (10–15 minutes)

Target: demonstrate that this is a *genuine* AI application — it dynamically
analyses new organisations/processes and produces explainable, prioritised
recommendations. No screenshots, no hard-coded answers.

**Prereqs:** backend on `http://localhost:8000`, dashboard on
`http://localhost:8501` (see README §8).

---

## 1. Explain the business problem (1 min)

> "Executives don't need another AI listicle. They need to know **where across
> their value chain AI creates the greatest value** — which processes, in what
> order, with what data, dependencies, people and risks. This system turns an
> organisation description and a set of processes into that answer, and — most
> importantly — it can be **told why**."

## 2. Show the architecture (1 min)

Open `docs/architecture.md` (or sketch the 5 layers). Emphasise the separation:
- UI → API → AI intelligence → data/knowledge → (optional) external research.
- **The LLM never decides the ranking** — scoring is a deterministic engine.
- **No hard-coded industries** — processes are matched to a *generic* value
  chain and capability catalogue via embeddings.

## 3. Create an organisation (1 min)

Dashboard → **Setup & Analyse** → fill in:
- Organisation: `ABC Retail`
- Industry: `Retail`
- Goals: `Reduce operating costs`, `Improve customer experience`

Click **Create Organisation**.

## 4. Add a process (1 min)

In the same page, add processes (one at a time):
- `Demand Forecasting` — "Forecast future demand to set stock levels"
- `Inventory Management`
- `Customer Support`
- `Supplier Management`
- `Marketing`
- `Order Fulfilment`

Each with a couple of pain points and available data.

## 5. Run AI analysis (1 min)

Click **🚀 Run AI Analysis**. Watch the spinner; note the log line that the
LLM provider resolved to `heuristic` (offline) — make the point that it runs
with *zero API keys or downloads*.

## 6. Show retrieved evidence (1 min)

Dashboard → scroll to an opportunity's **Explain Recommendation** expander →
"Evidence / sources". These are chunks retrieved from the knowledge base — real
reference content, not invented. Point out that uploaded documents would also
appear here.

## 7. Show a generated AI opportunity (1 min)

Open one opportunity card: business problem, AI capability, solution, data
requirements, roles, skills, risks — all structured and specific to that
process (e.g. *"Predictive Analytics for Demand Forecasting"*).

## 8. Show the scoring (1 min)

Point to the score gauge + the six-component breakdown. Show
`GET /api/config/scoring` (or the sidebar caption): the formula is visible and
weights are configurable.

## 9. Show explainability (1 min)

Read the breakdown labels: **FACT** (business problem, evidence, data),
**INFERENCE** (capability fit, expected value, risks), **RECOMMENDATION**
(final priority). Stress: *no unsupported claim is presented as fact.*

## 10. Show the dependency graph (1 min)

Dashboard → **Dependencies & Value Chain** → the dependency graph: opportunity
→ data → platform → API integration, plus shared-dependency conflicts.

## 11. Add a completely new process (1 min)

**Add Process** → enter something unseen, e.g.:
- Industry: `Healthcare`, Process: `Claims Processing`
- click **➕ Add & Analyse Process**

## 12. Prove no source-code change was required (1 min)

The new process is analysed live and produces a fresh, correct, industry-appropriate
analysis. Emphasise: *"There are no `if industry == 'healthcare'` branches — this
was matched against the generic capability catalogue at runtime."* Optionally run
`python backend/scripts/surprise_test.py` to show 4 industries in one go.

## 13. Explain scalability to 1,000+ processes (1 min)

- Caching avoids duplicate LLM calls; one structured call per process, not per
  capability; retrieval happens *before* generation to keep prompts small.
- Classification and scoring never touch the LLM (linear, deterministic).
- The orchestrator is a plain callable → dispatch through an async queue/worker
  pool; SQLite → PostgreSQL for concurrency.

## 14. Explain limitations & future improvements (1 min)

- Offline heuristic is grounded but not frontier-LLM fluent → add an API key.
- TF-IDF is lexical → `pip install -r requirements-optional.txt` enables
  semantic embeddings + Chroma.
- External web research is key-gated → plug in Tavily/Brave.
- Next: auth/multi-tenancy, async queue, React frontend.

**Total ≈ 14 minutes.**
