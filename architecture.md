# System Architecture — Unified RAG Capstone
## INFO5707 — Data Modeling

---

## System Overview

This document describes the architecture of the Unified RAG Capstone application built for INFO5707 — Data Modeling. The system integrates four database technologies with a large language model to demonstrate polyglot persistence — the practice of using multiple database types within a single system, each chosen for the kind of data it handles best.

The application is a teaching artifact. Every architectural decision was made with clarity and pedagogical value in mind, not just technical correctness.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Streamlit UI                         │
│  [ PostgreSQL ] [ MongoDB ] [ ChromaDB ] [ Neo4j ] [ Ask ]  │
└────────────┬────────────┬────────────┬────────────┬─────────┘
             │            │            │            │
             ▼            ▼            ▼            ▼
        ┌────────┐  ┌──────────┐ ┌─────────┐ ┌────────┐
        │Postgres│  │ MongoDB  │ │ChromaDB │ │ Neo4j  │
        │  SQL   │  │ Document │ │ Vector  │ │ Graph  │
        └────┬───┘  └────┬─────┘ └────┬────┘ └───┬────┘
             │            │            │           │
             └────────────┴────────────┴───────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │     Groq LLM Layer     │
                     │  (LangChain / LangGraph)│
                     │  - NL → SQL            │
                     │  - NL → Mongo Query    │
                     │  - NL → Embedding      │
                     │  - NL → Cypher         │
                     │  - Router + Synthesiser│
                     └────────────────────────┘
```

---

## Repository Structure

```
INFO5707/
├── rag_lab_1_postgre/          ← Lab 1 reference implementation (PostgreSQL)
├── rag_lab_2_mongo/            ← Lab 2 reference implementation (MongoDB)
├── rag_lab_3_chromadb/         ← Lab 3 reference implementation (ChromaDB + RAG)
├── rag_lab_4_neo4j/            ← Lab 4 folder (Neo4j introduced in capstone)
├── app.py                      ← Unified capstone application
├── pyproject.toml              ← UV dependency management
├── uv.lock                     ← Locked dependency versions (committed)
├── .env                        ← Team credentials (never committed)
├── .env.example                ← Credential template (committed)
├── architecture.md             ← This document (system-level)
├── CLAUDE_CODE_BRIEFING.md     ← Claude Code build instructions
├── RAG_Capstone_Team_Instructions.md  ← Student assignment document
├── RAG_Lab_Overview.md         ← Data modeling concepts overview
└── chroma_db/                  ← ChromaDB local persistence directory
```

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| UI | Streamlit | >=1.38.0 | Five-tab web interface |
| LLM Inference | Groq | API | Fast LLM inference, free tier |
| LLM Framework | LangChain | >=0.3.0 | LLM abstraction and tooling |
| Agent Workflow | LangGraph | >=1.0.0 | Retrieve → Generate state graph |
| Embeddings | sentence-transformers | >=3.0.0 | Local text embedding, no API key |
| Relational DB | PostgreSQL | Any | Structured, relational data |
| Document DB | MongoDB | Any | Flexible document data |
| Vector DB | ChromaDB | >=0.5.0 | Semantic vector search |
| Graph DB | Neo4j | Community | Relationship graph traversal |
| PG Driver | psycopg2-binary | >=2.9.0 | Python → PostgreSQL |
| Mongo Driver | pymongo | >=4.6.0 | Python → MongoDB |
| Neo4j Driver | neo4j | >=5.0.0 | Python → Neo4j |
| Dependency Mgmt | UV | Latest | Fast Python package management |
| Environment | python-dotenv | >=1.0.0 | .env credential loading |

---

## Application Structure — `app.py`

The application is organized into eleven sections in a single file:

```
# ── 1.  IMPORTS
# ── 2.  CONFIGURATION
# ── 3.  DATABASE CONNECTIONS
# ── 4.  CONNECTION HEALTH CHECK
# ── 5.  POSTGRESQL MODULE
# ── 6.  MONGODB MODULE
# ── 7.  CHROMADB MODULE
# ── 8.  NEO4J MODULE
# ── 9.  LANGGRAPH AGENT (ChromaDB)
# ── 10. ASK ANYTHING ROUTER
# ── 11. STREAMLIT UI
```

The single-file structure is intentional for a teaching context — students can read the entire application in one sitting without navigating a package hierarchy.

---

## Database Connection Architecture

### Lazy Connection Pattern

All four database connections use a lazy pattern decorated with `@st.cache_resource`. Connections are attempted only when first needed, not at application startup. Every connection function returns `None` on failure rather than raising an exception.

```
App Launch
    │
    ▼
UI Renders (all four tabs visible)
    │
    ▼
User opens a tab
    │
    ▼
Connection attempted (first access only)
    ├── Success → cached, green indicator in sidebar
    └── Failure → None returned, red indicator, friendly error in tab
```

This ensures the application is always launchable regardless of which databases are running — critical for a classroom setting where teams configure databases incrementally.

### Retry Mechanism

The sidebar provides a **Retry Connections** button that clears all four `@st.cache_resource` caches and reruns the health check. Teams use this after updating `.env` credentials without restarting the application.

---

## The Five Tabs

### Tab 1 — PostgreSQL
- **Purpose:** Natural language querying of structured relational data
- **LLM role:** Translates English questions into SQL using schema-aware prompting
- **Key feature:** Generated SQL is displayed alongside results — the translation is transparent
- **Schema source:** Dynamically queried from `information_schema.columns` at runtime
- **Teaching value:** Demonstrates schema-aware prompt engineering; shows why structured data belongs in a relational model

### Tab 2 — MongoDB
- **Purpose:** Natural language querying of flexible document data
- **LLM role:** Translates English questions into Python dict queries or aggregation pipelines
- **Key feature:** Collection selector adapts to whatever collections a team has created
- **Sample injection:** Three sample documents are passed to the LLM prompt so it knows actual field names
- **Teaching value:** Demonstrates few-shot prompting with real data; contrasts document modeling with relational modeling

### Tab 3 — ChromaDB
- **Purpose:** Document ingestion and semantic search over unstructured knowledge
- **Two modes:** Ingest (upload → chunk → embed → store) and Query (semantic search + LLM response)
- **LLM role:** Synthesises retrieved chunks into a grounded natural language answer
- **Hallucination guard:** Chunks below the similarity threshold are discarded; the LLM receives only relevant context
- **Teaching value:** Demonstrates the full RAG pipeline; introduces vector embeddings and cosine similarity as a data retrieval mechanism

### Tab 4 — Neo4j
- **Purpose:** Graph data loading and relationship traversal via natural language
- **Two modes:** Load (Cypher write statements) and Explore (natural language → Cypher → results)
- **LLM role:** Translates English questions into Cypher using schema introspection (labels, relationship types, properties)
- **Key feature:** Graph schema is dynamically retrieved using `CALL db.labels()` and `CALL db.relationshipTypes()`
- **Teaching value:** Introduces a fourth data model; demonstrates why connected data is painful in SQL but natural in Cypher

### Tab 5 — Ask Anything
- **Purpose:** Cross-database intelligent routing and synthesis
- **LLM role:** Used twice — once as a router (which databases to query) and once as a synthesiser (combine results into one answer)
- **Reasoning trace:** The tab displays which databases were queried and the LLM's routing rationale — the primary teaching artifact of the entire application
- **Routing logic:** Groq returns a JSON object specifying which connected databases are relevant to the question; fallback queries all connected databases if JSON parsing fails
- **Teaching value:** Shows polyglot persistence in action; makes the architectural decision visible and explainable

---

## The LLM Layer

### Model Configuration
- **Default model:** `llama-3.1-8b-instant` via Groq
- **Fallback:** `llama3.2` via Ollama (local, no API key required)
- **Provider switching:** Controlled by `LLM_PROVIDER` in `.env` — no code changes required
- **Caching:** The LLM client is loaded once per session via `@st.cache_resource`

### LangGraph Agent (ChromaDB Tab)

The ChromaDB tab uses a two-node LangGraph state graph:

```
[START] → retrieve_node → generate_node → [END]
```

- **retrieve_node:** Embeds the query, searches ChromaDB, returns top-k chunks above the similarity threshold
- **generate_node:** Receives chunks as context, calls the LLM with a grounding system prompt, returns a cited response
- **Hallucination guard:** If `no_context_found` is True, generate_node returns a safe fallback message without calling the LLM

### Prompt Engineering Patterns Used

| Tab | Pattern | Description |
|---|---|---|
| PostgreSQL | Schema injection | Full `information_schema` output inserted into prompt |
| MongoDB | Few-shot with real data | Sample documents inserted to show actual field names |
| ChromaDB | Context grounding | Retrieved chunks inserted as system-level context |
| Neo4j | Schema injection | Labels, relationship types, and properties inserted |
| Ask Anything | Structured output | LLM instructed to return JSON for reliable parsing |

---

## Environment Configuration

All credentials and configuration are managed through a `.env` file that is never committed to version control. The `.env.example` file documents every required key.

### Required Variables

```
LLM_PROVIDER          groq or ollama
GROQ_API_KEY          Groq console API key
GROQ_MODEL            LLM model name
POSTGRES_HOST         Database server hostname
POSTGRES_PORT         Default 5432
POSTGRES_DB           Database name
POSTGRES_USER         Username
POSTGRES_PASSWORD     Password
MONGO_URI             Connection string
MONGO_DB              Database name
CHROMA_PERSIST_PATH   Local directory for ChromaDB files
CHROMA_COLLECTION     Collection name
NEO4J_URI             bolt:// or neo4j+s:// URI
NEO4J_USER            Default: neo4j
NEO4J_PASSWORD        Set on first login
```

---

## Known Dependency Considerations

- **`transformers` must be pinned below 4.47.0** — newer versions include vision models that import `torchvision` at scan time, causing Streamlit's file watcher to log hundreds of `ModuleNotFoundError` warnings
- **`unstructured` is excluded** — this package pulls in PyTorch dependencies that are unnecessary for text and PDF loading; `TextLoader` handles markdown files directly
- **`sentence-transformers` downloads ~90MB on first run** — the `all-MiniLM-L6-v2` embedding model is cached locally after the first download; run `uv sync` and launch the app once before any class session

---

## Design Principles

- **Lazy over eager** — no database connection is attempted until a tab is first used
- **Transparent over magic** — generated SQL, Mongo queries, and Cypher are always displayed alongside results
- **Graceful degradation** — the application remains functional when any database is unavailable
- **Teaching notes over terseness** — every non-obvious decision is annotated with a `# Teaching note:` comment
- **One file over packages** — the single `app.py` structure prioritizes readability over engineering best practices for a teaching context
- **Schema-driven prompts** — LLM prompts use dynamically retrieved schema, not hardcoded descriptions, so the system works for any team's data

---

## Instructor Notes

- The four lab reference folders are preserved intact and should not be modified — they serve as student reference implementations
- Neo4j has no standalone lab reference — the capstone is where Neo4j is introduced; teams should expect to spend more time on the Load mode setup
- The `eval()` call in the MongoDB module is intentional and annotated as a teaching moment about LLM-generated code execution risks
- The Ask Anything routing fallback (query all connected databases) is intentional defensive design — partial failure should not produce a silent empty response
- ChromaDB data persists to disk at `CHROMA_PERSIST_PATH` — remind teams to clear this directory when switching business scenarios

---

*INFO5707 — Data Modeling | System Architecture Document v1.0*
