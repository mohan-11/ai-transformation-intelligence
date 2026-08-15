# Data Model

Relational model (SQLAlchemy ORM). The AIOpportunity is normalised: scalar
business facts live in typed columns; list-valued qualitative fields are JSON
columns; roles, skills and dependencies are separate tables.

## Entities

### Industry
`id, name (unique), slug (unique), description`
→ one-to-many with Organisation.

### Organisation
`id, name, industry_id (FK→Industry), industry_name, description,
business_goals (JSON list), created_at, updated_at`
→ one-to-many with Process, Analysis, Document.

### Process
`id, organisation_id (FK), name, description, business_objective, industry,
current_technology, pain_points (JSON), available_data (JSON),
value_chain_area, value_chain_category, created_at, updated_at`
→ one-to-many with Activity and AIOpportunity.

### Activity
`id, process_id (FK), name, description`
→ many-to-one with Process.

### Document / Chunk
`Document: id, organisation_id (FK, nullable), filename, title, source,
industry, content_type, created_at`
`Chunk: id, document_id (FK), text, page, section, meta (JSON)`
→ one-to-many Document→Chunk. Chunks are embedded in the vector store keyed by
a chunk id.

### Source / ResearchFinding
`Source: id, title, url, source_type, industry, retrieved_at`
`ResearchFinding: id, analysis_id (FK), opportunity_id (FK, nullable), title,
summary, url, source_type, evidence_level`

### AIOpportunity
`id, analysis_id (FK), organisation_id (FK), process_id (FK, nullable)`
- identity/classification: `title, description, industry, value_chain_area,
  process, activity`
- problem→solution: `business_problem, ai_solution, ai_capability`
- value/complexity: `expected_business_value, value_score,
  implementation_complexity, complexity_score`
- data: `data_requirements (JSON), data_availability, technology_requirements
  (JSON)`
- people/skills: `affected_roles (JSON), required_skills (JSON)` — also
  normalised via association tables to Role and Skill
- deps/risk/governance: `dependencies (JSON), risks (JSON),
  governance_considerations (JSON)`
- scores: `priority_score, confidence_score` + six component columns
  (business_value/strategic_alignment/data_readiness/feasibility/complexity/
  risk)
- evidence/explanation: `evidence (JSON), sources (JSON), explanation`
- `created_at, updated_at`

### Role / Skill (with association tables)
`Role: id, name (unique), description`
`Skill: id, name (unique), description`
`opportunity_roles(opportunity_id, role_id)`, `opportunity_skills(...)`
→ many-to-many with AIOpportunity.

### Dependency
`id, analysis_id (FK), source_type, source_id, source_label, target_type,
target_id, target_label, dependency_type (data|technology|people|implementation),
description`
→ represents explicit dependencies; the NetworkX graph is also derived from
AIOpportunity.dependencies.

### Analysis
`id, organisation_id (FK), status (pending|running|completed|failed), summary,
config (JSON), error, created_at, completed_at`
→ one-to-many with AIOpportunity, Recommendation, ResearchFinding.

### Recommendation
`id, analysis_id (FK), opportunity_id (FK), rank, phase (quick_win|medium_term|
strategic), timeframe, rationale, created_at`

### Feedback
`id, opportunity_id (FK), rating (1–5), comment, created_at`

## Relationships (overview)

```
Industry 1─* Organisation 1─* Process 1─* Activity
                       │            1─* AIOpportunity *─* Role
                       │                       *─* Skill
                       │                       1─* Dependency
                       │
                       1─* Analysis 1─* AIOpportunity
                          │          1─* Recommendation
                          │          1─* ResearchFinding
                          │
                       1─* Document 1─* Chunk
```

## Storage notes

- SQLite by default; PostgreSQL-ready (generic JSON/Text/Float types, no
  dialect-specific constructs).
- JSON columns hold *lists* of genuinely list-valued fields (risks, data
  requirements, evidence, sources) — the rest is relational.
- Timestamps are timezone-aware UTC.
