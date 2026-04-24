# RAG Lab Overview
## INFO5707 — Data Modeling
### A Multi-Database Retrieval-Augmented Generation System

---

## Why This Lab Matters for Data Modeling Students

- Most data modeling courses teach one database paradigm — this lab teaches **four simultaneously**, forcing you to think about *why* data models differ
- You are not just learning syntax — you are learning to **match a data problem to a data model**, which is the core skill of a working data engineer or architect
- Every enterprise system you will work in after graduation uses multiple database types — this lab is a miniature version of that reality
- The LLM layer adds a dimension no traditional data course covers — **natural language as a query interface** — which is rapidly becoming a production expectation
- Building a system that integrates four databases teaches **system thinking**, not just table design
- The capstone business scenario forces you to make **architectural decisions and defend them** — exactly what senior engineers and architects do in design reviews

---

## How This Lab Benefits Job-Seeking Graduate Students

- **Portfolio differentiation** — most candidates know SQL; very few have built a working system combining relational, document, vector, and graph databases
- **Interview readiness** — you can speak concretely to trade-offs between data models, which is a standard senior-level interview topic
- **LLM integration experience** — Groq, LangChain, and RAG architecture are appearing in nearly every data engineering and ML engineering job description in 2025–2026
- **Full-stack data exposure** — you touch ingestion, storage, retrieval, and generation in one project
- **Cloud-adjacent skills** — PostgreSQL, MongoDB Atlas, and Neo4j Aura all have cloud-managed versions; what you learn locally transfers directly
- **Python data ecosystem fluency** — psycopg2, pymongo, chromadb, neo4j driver, LangChain, Streamlit, and UV are all real production tools
- **Architectural storytelling** — the `architecture.md` deliverable teaches you to explain system design in writing, a skill most technical graduates lack
- **Demonstrated judgment** — choosing the right database for the right data is a senior-level skill; this lab forces you to practice it at the graduate level

---

## PostgreSQL — The Relational Foundation

### What It Is
- A **relational database management system (RDBMS)** based on the relational model introduced by E.F. Codd in 1970
- Open-source, ACID-compliant, and the most widely deployed advanced open-source database in enterprise settings

### Key Data Modeling Concepts
- **Schema** — a defined, enforced structure of tables, columns, and data types that all data must conform to
- **Tables and rows** — data is organized into relations (tables) with tuples (rows) and attributes (columns)
- **Primary key** — a unique identifier for each row; the anchor of relational integrity
- **Foreign key** — a column that references a primary key in another table, enforcing **referential integrity**
- **Normalization** — the process of organizing data to reduce redundancy (1NF, 2NF, 3NF, BCNF)
- **Joins** — the mechanism for combining related data across tables (INNER, LEFT, RIGHT, FULL OUTER)
- **Indexes** — data structures that accelerate query performance at the cost of write overhead
- **Transactions** — a unit of work that is atomic, consistent, isolated, and durable (ACID)
- **Views** — virtual tables based on a query, useful for abstraction and security
- **Constraints** — rules enforced at the database level (NOT NULL, UNIQUE, CHECK, DEFAULT)

### Key Terminology
- **DDL** (Data Definition Language) — CREATE, ALTER, DROP
- **DML** (Data Manipulation Language) — SELECT, INSERT, UPDATE, DELETE
- **Query planner** — the engine that decides how to execute a SQL query
- **psycopg2** — the Python driver used to connect to PostgreSQL

### In This Lab
- Stores structured, consistent business records (the "system of record")
- Groq translates natural language questions into SQL
- The schema viewer in the app demonstrates how schema introspection works programmatically
- Teaches why **structured data with relationships belongs in a relational model**

---

## MongoDB — The Document Store

### What It Is
- A **NoSQL document database** that stores data as JSON-like documents (BSON internally)
- Designed for flexibility, horizontal scalability, and developer speed
- Part of the broader **NoSQL movement** that emerged when relational models proved too rigid for web-scale applications

### Key Data Modeling Concepts
- **Document** — the base unit of storage; a self-contained JSON object that can have nested fields and arrays
- **Collection** — a group of documents, analogous to a table but without an enforced schema
- **Schema flexibility** — documents in the same collection can have different fields; there is no DDL required
- **Embedding vs. referencing** — the core MongoDB modeling decision: nest related data inside a document (embedding) or reference it by ID (referencing)
- **Denormalization** — intentionally duplicating data to optimize for read performance, the opposite of relational normalization
- **Aggregation pipeline** — a multi-stage data transformation framework for complex queries ($match, $group, $sort, $project, $lookup)
- **Index types** — single field, compound, multikey (for arrays), text, geospatial, and wildcard indexes
- **Sharding** — horizontal partitioning of data across multiple servers for scale
- **Replica sets** — a group of MongoDB instances that maintain the same dataset for high availability

### Key Terminology
- **BSON** — Binary JSON, the internal storage format
- **ObjectId** — MongoDB's default unique identifier for documents
- **pymongo** — the Python driver used in this lab
- **$match, $group, $lookup** — common aggregation pipeline operators
- **Schema-on-read** vs **schema-on-write** — MongoDB enforces structure at read time (your application), not write time

### In This Lab
- Stores flexible, variable-structure business data (logs, notes, records that vary by type)
- Groq generates Python dict-style queries and aggregation pipelines
- Teaches **when schema flexibility is an architectural advantage**, not just laziness
- Demonstrates the embedding vs. referencing trade-off in practice

---

## ChromaDB — The Vector Store

### What It Is
- An **open-source vector database** purpose-built for storing and retrieving text embeddings
- The data persistence layer for **Retrieval-Augmented Generation (RAG)** systems
- Part of a new class of databases that emerged with the rise of large language models

### Key Data Modeling Concepts
- **Embedding** — a numerical vector (list of floating point numbers) that represents the semantic meaning of a piece of text
- **Vector space** — a high-dimensional mathematical space where semantically similar texts are close together
- **Cosine similarity** — the primary distance metric for comparing text embeddings; measures the angle between two vectors
- **Chunking** — splitting large documents into smaller pieces before embedding; chunk size and overlap are deliberate design choices
- **Collection** — ChromaDB's storage unit, analogous to a table; holds documents, their embeddings, and metadata
- **Metadata filtering** — the ability to combine semantic search with structured filters (e.g., "find similar text, but only from documents uploaded this week")
- **HNSW index** — Hierarchical Navigable Small World, the approximate nearest neighbor algorithm ChromaDB uses for fast similarity search
- **Retrieval** — the process of finding the top-k most semantically similar chunks for a given query
- **Similarity threshold** — a minimum score below which retrieved chunks are discarded; the primary hallucination guard in RAG

### Key Terminology
- **RAG** (Retrieval-Augmented Generation) — the pattern of retrieving relevant context before generating a response
- **Embedding model** — the model that converts text to vectors; this lab uses `all-MiniLM-L6-v2` from sentence-transformers
- **Top-k retrieval** — returning the k most similar results for a query
- **Persistent vs. ephemeral client** — whether the vector store survives application restarts
- **Duplicate detection** — using content hashing to prevent the same document from being ingested twice

### In This Lab
- Stores knowledge base documents (policies, manuals, research) as vectors
- Enables semantic search — finding relevant content even when exact keywords don't match
- The ingestion pipeline (load → chunk → embed → store) is the core RAG engineering pattern
- Teaches **a fundamentally different data model** — similarity-based retrieval vs. exact-match queries
- Demonstrates why **unstructured knowledge requires a different storage paradigm** than records or documents

---

## Neo4j — The Graph Database

### What It Is
- A **native graph database** that stores data as nodes (entities) and relationships (connections between entities)
- Based on **property graph model** — nodes and relationships can both carry properties
- The right tool when the **connections between data are as important as the data itself**

### Key Data Modeling Concepts
- **Node** — an entity in the graph (a person, product, location, concept); equivalent to a record in relational terms
- **Relationship** — a directed, named connection between two nodes (e.g., `[:KNOWS]`, `[:PURCHASED]`, `[:REPORTS_TO]`)
- **Property** — a key-value pair stored on a node or relationship (e.g., `name: "Alice"`, `since: 2023`)
- **Label** — a tag on a node that identifies its type (e.g., `:Person`, `:Product`); nodes can have multiple labels
- **Traversal** — the act of following relationships from node to node; the fundamental graph query operation
- **Path** — a sequence of nodes and relationships; graph queries return paths, not rows
- **Graph schema** — more flexible than relational; defined by the labels and relationship types you create, not a DDL
- **Cypher** — Neo4j's declarative query language; designed to visually represent graph patterns
- **Index** — created on node properties to speed up lookup (e.g., find all `:Person` nodes where `name = "Alice"`)
- **MERGE** — a Cypher clause that creates a node or relationship only if it doesn't already exist; critical for avoiding duplicates

### Key Terminology
- **Cypher** — the query language (`MATCH`, `CREATE`, `MERGE`, `RETURN`, `WHERE`, `WITH`)
- **MATCH** — the Cypher equivalent of SELECT; finds patterns in the graph
- **Pattern matching** — describing the shape of the data you want to find using ASCII art-like syntax: `(a)-[:KNOWS]->(b)`
- **Graph algorithms** — PageRank, shortest path, community detection; built into Neo4j's Graph Data Science library
- **Neo4j Aura** — the cloud-managed version of Neo4j (free tier available)
- **neo4j Python driver** — the library used to connect and run Cypher from Python

### In This Lab
- Stores relationship-heavy data where traversal queries matter
- Groq translates natural language into Cypher queries
- The Load mode teaches node and relationship creation; the Explore mode teaches traversal queries
- Teaches **a fourth data model** — one where the structure of connections is the primary design concern
- Demonstrates why **graph data is painful to query in SQL** (recursive CTEs) but natural in Cypher

---

## The LLM Layer — Groq + LangChain

### What It Is
- **Groq** — a cloud inference platform offering extremely fast LLM inference on dedicated hardware; free tier available
- **LangChain** — a Python framework for building LLM-powered applications; provides abstractions over models, prompts, chains, and agents
- **LangGraph** — an extension of LangChain for building stateful, graph-based agent workflows
- The LLM layer in this lab serves as a **universal query translator and synthesiser**

### How the LLM Fits Into the Data Model Picture
- Acts as a **natural language interface** to all four databases — users ask questions in English, the LLM generates the appropriate query
- For PostgreSQL: English → SQL
- For MongoDB: English → Python dict / aggregation pipeline
- For ChromaDB: English → embedding query → context retrieval → grounded response
- For Neo4j: English → Cypher
- In the Ask Anything tab: English → routing decision → multi-database query → synthesised answer

### Key Concepts
- **Prompt engineering** — crafting the input to the LLM to produce reliable, structured output; this is a data modeling problem as much as an NLP problem
- **Schema-aware prompting** — injecting the actual database schema into the prompt so the LLM can generate valid queries without hallucinating column names
- **Few-shot prompting** — providing real sample documents or rows to the LLM so it knows the actual data structure
- **Hallucination** — when an LLM generates confident but incorrect information; the similarity threshold and grounding rules in this lab are defenses against it
- **RAG pattern** — Retrieve relevant context first, then Generate a response grounded in that context; the alternative to relying on the LLM's parametric memory alone
- **LangGraph state machine** — the retrieve → generate pipeline is modeled as a directed graph with shared state; separation of concerns by design
- **Inference speed** — Groq's hardware acceleration makes real-time LLM queries practical in a classroom setting on a free tier

### Key Terminology
- **LLM** (Large Language Model) — a neural network trained on large text corpora to generate and understand language
- **Token** — the unit of text an LLM processes; roughly 0.75 words
- **Context window** — the maximum number of tokens an LLM can process at once; limits how much schema or document content you can include in a prompt
- **System prompt** — instructions given to the LLM before the user message; defines the model's role and constraints
- **Grounding** — anchoring the LLM's response to retrieved facts rather than general knowledge
- **`@st.cache_resource`** — Streamlit's mechanism for loading the LLM once per session, not on every user interaction

---

## Key Architectural Concepts Across the Entire Lab

- **Polyglot persistence** — using multiple database types in one system, each chosen for what it does best; this lab is a working implementation of that pattern
- **Lazy connection pattern** — deferring database connections until they are needed, so the application remains functional even when some backends are unavailable
- **Separation of concerns** — the retrieval logic (what data to fetch) is separated from the generation logic (what to say about it)
- **Environment variables** — credentials and configuration are never hardcoded; the `.env` file pattern is universal in production systems
- **Dependency management** — UV and `pyproject.toml` pin exact package versions so the system behaves identically across machines
- **Session state** — Streamlit's mechanism for persisting data across UI interactions; analogous to server-side session management in web development

---

## Future Directions for a Lab Like This

### Near-Term Enhancements
- **Authentication layer** — add user login so different teams or users see different data; teaches role-based access control across database types
- **Data lineage tracking** — log which database answered which query and with what confidence; a real production concern
- **Streaming responses** — replace batch LLM calls with streaming so responses appear token by token, improving perceived performance
- **Structured output enforcement** — use LLM function calling or JSON mode to guarantee parseable query output, eliminating the eval() pattern in the MongoDB module
- **Evaluation framework** — add automated testing of LLM-generated queries against known correct answers; introduces the concept of LLM evals

### Medium-Term Directions
- **Cloud deployment** — deploy the app to Streamlit Community Cloud, connecting to managed database services (Supabase for Postgres, MongoDB Atlas, Neo4j Aura); teaches cloud data architecture
- **Real-time data ingestion** — add a Kafka or webhook layer so databases update live; introduces streaming data modeling
- **Cross-database joins** — extend the Ask Anything tab to perform genuine multi-database result merging, not just parallel queries; a research-active problem
- **Graph-enhanced RAG** — use Neo4j to store relationships between ChromaDB chunks, creating a knowledge graph that improves retrieval precision
- **Multi-modal ingestion** — extend ChromaDB ingestion to handle images and audio, not just text; introduces embedding models beyond language

### Advanced / Research Directions
- **Agentic data pipelines** — replace the static tab structure with a fully autonomous LangGraph agent that decides how to retrieve, transform, and synthesise data without user guidance
- **Schema evolution management** — add tooling that detects when a team changes their database schema and automatically updates the LLM prompts; a real DevOps challenge
- **Federated query optimization** — research how to optimally split a query across four databases, minimizing latency and token usage
- **Fine-tuning for domain-specific query generation** — fine-tune a small model on a team's specific schema to improve SQL and Cypher generation accuracy
- **Privacy-preserving RAG** — add differential privacy or data masking to the retrieval layer; critical for healthcare and finance scenarios
- **Benchmarking query quality** — build a framework that scores LLM-generated SQL, Cypher, and MongoDB queries against ground truth; introduces MLOps concepts

---

*INFO5707 — Data Modeling | RAG Lab Overview*