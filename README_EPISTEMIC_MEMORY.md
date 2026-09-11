# AletheiaTelos Epistemic Memory Integration Boundary

## Purpose

This document defines the initial Epistemic Memory / Institutional Learning boundary for AletheiaTelos using `CHARTER.md` as the governing constitution and `FUTURE_STATE_ARCHITECTURE.md` as the destination architecture.

Second Brain OS is treated as a substrate/reference implementation. It does not become the governing architecture of AletheiaTelos.

The objective is institutional memory that preserves what was known, believed, decided, observed, and learned without becoming an authority layer.

## Architectural conclusion

The existing AletheiaTelos architecture already contains the correct analytical spine and learning boundary:

`EVIDENCE -> INTEGRITY -> COMPUTATIONAL KALEIDOSCOPE -> CONFLICT ANALYSIS -> INDEPENDENT MONTE CARLO -> SKEPTIC -> SYNTHESIS -> GOVERNANCE -> OBSERVER -> EPISTEMIC MEMORY`

The existing learning loop also preserves immutable forecasts and separate resolution records. Learning is informational only and does not automatically change authority, weights, execution permissions, brokerage access, or portfolio state.

Therefore the smallest justified implementation now is a **memory contract and integration boundary**, not a new database, vector store, graph engine, or parallel analytical pipeline.

## Epistemic taxonomy

AletheiaTelos must preserve these distinct classes:

`EVIDENCE != KNOWLEDGE != ASSUMPTION != HYPOTHESIS != CALCULATION != INTERPRETATION != RECOMMENDATION != AUTHORIZATION != OUTCOME`

Memory may reference each class, but must not collapse them into a generic memory record.

Memory stores analytical artifacts and their provenance. Existing analytical engines remain responsible for calculations.

## Second Brain OS integration manifest

| Second Brain component | Relevant implementation | Classification | AletheiaTelos destination | CRE adaptation | Governance / historical state | Access mode |
|---|---|---|---|---|---|---|
| Raw source archive | `vault-template/raw/` | ADAPT | Evidence/source boundary | Preserve source identity, dates, retrieval, applicability, freshness and verification | Raw material is not truth; preserve original source | READ-ONLY after capture |
| Source pages | `vault-template/wiki/sources/`, `skills/second-brain-ingest/SKILL.md` | ADAPT | Evidence-linked source records | Attach claims to source evidence and preserve point-in-time context | Never silently upgrade interpretation to evidence | MEMORY-WRITING under controlled workflow |
| Wiki knowledge layer | `vault-template/wiki/` | ADAPT | Institutional knowledge layer | Knowledge must remain distinct from evidence and assumptions | Preserve provenance and supersession history | ANALYTICAL / MEMORY-WRITING |
| Concepts | Wiki concept pages and ingest skill | ADAPT | Markets, risks, asset concepts, financing concepts, operating patterns | Use institutional CRE ontology rather than personal knowledge ontology | Preserve source lineage | ANALYTICAL / MEMORY-WRITING |
| Entities | Wiki entity pages | ADAPT | Properties, tenants, sponsors, brokers, lenders, loans, markets | Structured identity and relationships should be preferred over free-form notes | Historical identity and relationship changes must remain attributable | ANALYTICAL / MEMORY-WRITING |
| Project layer | `vault-template/projects/` | ADAPT | Investment opportunity / transaction context | Map Inputs/Process/Outputs/Feedback onto the existing investment lifecycle | Historical case state must remain reconstructable | ANALYTICAL / MEMORY-WRITING; human gates remain separate |
| Inputs | Project pipeline | ADAPT | Evidence + Opportunity | Consume existing evidence and opportunity ingestion boundaries | Inputs retain source/provenance | READ-ONLY to analytical layers |
| Process | Project pipeline | ADAPT | Screening, underwriting, scenarios, simulation, contrarian, capital stack, synthesis | Existing engines remain authoritative for their calculations | No memory-derived process may override engine boundaries | ANALYTICAL |
| Outputs | Project pipeline | ADAPT | Structured Investment Case / recommendation | Reference existing backend outputs rather than duplicate them | Recommendation remains distinct from authorization | ANALYTICAL |
| Feedback | Project pipeline | ADAPT | Observer / Outcome / Attribution / Learning | Capture actual performance against original case | Outcome cannot rewrite prior belief | MEMORY-WRITING |
| Bidirectional linking | `skills/second-brain-ingest/SKILL.md` | IMPORT | Institutional relationship graph | Link opportunities, evidence, claims, assumptions, decisions, outcomes and lessons | Links must preserve provenance and historical meaning | ANALYTICAL / MEMORY-WRITING |
| Contradiction preservation | `commands/contradictions.md`, ingest skill | IMPORT | Contradiction records | Preserve conflicting evidence, interpretations and agent conclusions with dates and sources | Consensus is never truth; unresolved conflicts remain visible | READ-ONLY query / MEMORY-WRITING record |
| Changed-mind history | `commands/changed-my-mind.md` | ADAPT | Epistemic revision history | Record what changed, when, why, and what evidence moved the position | Never rewrite the earlier position | READ-ONLY query / MEMORY-WRITING record |
| Ingestor agent | `agents/ingestor.md` | ADAPT | Evidence-to-knowledge ingestion | Must not resolve ambiguous claims or manufacture conclusions | Historical source context preserved | MEMORY-WRITING |
| Curator agent | `agents/curator.md` | IMPORT | Memory maintenance proposals | Candidate archival/merge actions must respect institutional retention and audit rules | Proposals only; no destructive deletion by default | READ-ONLY |
| Researcher agent | `agents/researcher.md` | ADAPT | Institutional memory research | Retrieve precedent and evidence without becoming an authority | Retrieved knowledge remains attributable | READ-ONLY / ANALYTICAL |
| Linker agent | `agents/linker.md` | ADAPT | Relationship maintenance | Suggest and maintain structured institutional links | Cannot change meaning of historical records | ANALYTICAL / MEMORY-WRITING |
| Reviewer agent | `agents/reviewer.md` | ADAPT | Memory/evidence quality review | Check provenance, contradictions, gaps and schema integrity | Review cannot erase disagreement | READ-ONLY / ANALYTICAL |
| Graph analyst | `agents/graph-analyst.md` | ADAPT | Institutional relationship analysis | Analyze connected opportunities, risks, lenders, markets and outcomes | Graph relationships do not become truth by connectivity | ANALYTICAL |
| Skills | `skills/` | ADAPT | Institutional workflows | Convert only justified workflows into CRE-specific skills | Skills are procedures, not authority | Depends on workflow |
| Commands | `commands/` | ADAPT | Scoped memory/research operations | Replace generic PKM commands with auditable institutional operations | Consequential operations require authorization | Depends on command |
| Maintenance / linting | `scripts/` and maintenance docs | IMPORT | Memory integrity checks | Check provenance, orphaned records, broken links, stale claims, unresolved contradictions and missing outcomes | Maintenance cannot silently delete institutional history | READ-ONLY / MEMORY-WRITING only for safe metadata |
| Git history | Repository history | IMPORT | Immutable development/audit lineage | Use application-level records for decision history, Git for implementation history | Git history does not replace epistemic records | READ-ONLY |
| Vector database | Second Brain design rule | REJECT for now | None | No concrete retrieval requirement currently justifies it | Avoid infrastructure novelty | N/A |
| Personal PKM ontology | `vault-template` personal conventions | REJECT | None | AletheiaTelos requires institutional CRE ontology | Charter and future-state architecture govern | N/A |

## Institutional project model

The Second Brain project pattern maps to AletheiaTelos as:

`INPUTS -> EVIDENCE / OPPORTUNITY`

`PROCESS -> SCREENING / UNDERWRITING / SCENARIOS / SIMULATION / CONTRARIAN / CAPITAL STACK / SYNTHESIS`

`OUTPUTS -> STRUCTURED INVESTMENT CASE / RECOMMENDATION / HUMAN DECISION`

`FEEDBACK -> OBSERVER / OUTCOME / ATTRIBUTION / LEARNING`

`LEARNING -> NEXT OPPORTUNITY`

No second project-management architecture should be introduced.

## Minimum institutional memory objects

The future memory subsystem should be able to represent at minimum:

- `EvidenceRecord`
- `KnowledgeRecord`
- `ClaimRecord`
- `AssumptionRecord`
- `HypothesisRecord`
- `InterpretationRecord`
- `DecisionRecord`
- `AuthorizationRecord`
- `OutcomeRecord`
- `AttributionRecord`
- `LessonRecord`
- `ContradictionRecord`
- `RelationshipRecord`

These are conceptual boundaries at this stage. They do not require immediate persistence implementation.

Each material record should support, where applicable:

- stable identifier
- record type
- created/observed/effective timestamps
- source references
- provenance
- status
- confidence or uncertainty where appropriate
- related records
- supersedes/superseded-by relationships
- contradiction relationships
- decision context
- outcome context

## Historical epistemic state

AletheiaTelos must preserve point-in-time state rather than overwrite it.

The minimum historical chain is:

`WHAT WAS KNOWN -> WHAT WAS BELIEVED -> WHY -> SUPPORTING EVIDENCE -> DISSENT -> DECISION -> AUTHORIZATION -> OUTCOME -> ATTRIBUTION -> LESSON`

A later observation may supersede a claim or demonstrate that an assumption was wrong. It must not rewrite the earlier record so that the institution appears to have known the later information at the earlier decision date.

## Contradiction model

Contradictions remain first-class records.

Example:

- Broker claim: occupancy 96%
- Property manager claim: occupancy 91%
- Lease evidence: occupancy 88%
- Underwriting assumption: occupancy 91%
- Contrarian finding: stabilization assumption insufficiently supported

The system should preserve each position, its source and dates, the relationship between them, and what evidence would resolve the conflict if known.

The system must not force a single answer merely to make synthesis cleaner.

## Access and authority model

### Read-only

- retrieve institutional precedent
- inspect evidence
- inspect historical decisions
- inspect contradictions
- inspect outcomes
- inspect lessons
- inspect graph relationships

### Analytical

- classify records
- identify links
- detect contradictions
- identify stale evidence
- compare prior assumptions with current evidence
- surface precedent
- propose lessons

### Memory-writing

- record evidence metadata
- record claims and relationships
- append decisions and dissent
- record outcomes
- record attribution
- record lessons
- record approved corrections or supersession

### Human-authorized

- consequential investment decisions
- capital commitments
- transaction authorization
- execution
- changes to governance
- changes to authority boundaries
- destructive historical deletion

Memory itself has no authority.

## Institutional learning loop

The intended long-term loop is:

`SOURCE -> INGEST -> SCREEN -> UNDERWRITE -> SCENARIO -> SIMULATE -> ATTACK -> STRUCTURE -> SYNTHESIZE -> AUTHORIZE -> EXECUTE -> ACQUIRE -> OPERATE -> OBSERVE -> ATTRIBUTE -> LEARN -> FIND AGAIN`

Second Brain mechanisms make the final segment operational by providing linked knowledge, contradiction preservation, scoped project context, maintenance, and repeatable memory workflows.

## Build now

1. Establish this Epistemic Memory contract and architecture boundary.
2. Preserve the existing immutable prediction/resolution learning mechanism.
3. Define stable conceptual record boundaries for evidence, knowledge, assumptions, decisions, outcomes, attribution and lessons.
4. Ensure future memory work references existing analytical outputs instead of duplicating them.
5. Add tests only when the first concrete memory persistence implementation is introduced.

## Build later

- concrete persistence for institutional memory records
- structured relationship graph
- institutional precedent retrieval
- contradiction query workflows
- changed-belief / changed-mind reports
- memory maintenance and integrity tooling
- Observer-to-memory adapters
- outcome attribution persistence
- cross-deal pattern detection
- memory-aware Computational Kaleidoscope retrieval

## Do not build now

- generic personal second-brain vault
- second project-management system
- parallel underwriting engine
- parallel simulation engine
- financial calculations inside memory
- autonomous lender selection
- autonomous transaction execution
- vector database without demonstrated need
- memory-driven authority or self-authorization
- destructive historical rewriting

## Governance

`CHARTER.md` remains unchanged and supreme.

The memory boundary follows these Charter principles:

- evidence before assertion
- truth before consensus
- visible uncertainty
- preservation of disagreement
- human authority over consequential decisions
- tools are capabilities, not permissions
- historical beliefs remain attributable to their original context
- learning is not authority
- system improvement cannot redefine its own governing boundaries

No memory implementation may weaken these constraints.

## Validation boundary

The current repository already documents that forecasts remain immutable, later outcomes are separate resolution records, and learning is informational only. The full decision-intelligence path also keeps simulation independent from agent conclusions and exposes no brokerage, order, credential, or portfolio mutation capability.

The initial Epistemic Memory work therefore does not require modification of certified analytical engines.

The next implementation phase should add persistence and adapters only after the record contract is reviewed and the existing test suite remains green.
