# INFO5707 — RAG-LAB


Multi-database RAG application for INFO5707. Integrates PostgreSQL, MongoDB, ChromaDB, and Neo4j with a Groq LLM layer via a single Streamlit interface.

## Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run `uv sync` to install dependencies
4. Run `uv run streamlit run app.py`

## Requirements

- Python 3.11–3.12
- UV package manager
- PostgreSQL, MongoDB, and Neo4j instances
- Groq API key (free at console.groq.com)

## Team Assignment Instructions

---

## Overview

Throughout this course you have built four separate lab applications, each introducing a different database technology. For this capstone project, your team will design a **real business scenario** and build a single unified application that uses all four databases together — each one doing the job it was designed to do.

The result is a multi-database RAG (Retrieval-Augmented Generation) system powered by Groq that demonstrates not just how to use these tools, but *why* you would choose each one in a professional setting.

---

## Team Formation

- Teams of **3 to 5 students**
- Each team member should be able to speak to any part of the system during a demo
- You are encouraged to divide ownership of the four database modules, but the final application must work as a unified whole

---

## Step 1 — Design Your Business Scenario

Before writing a single line of code, your team must define a business scenario that **genuinely requires all four database types**. This is not a cosmetic exercise. The scenario should create natural, defensible reasons to use each database.

### The Four Databases and Their Roles

| Database | Strength | Typical Use |
|---|---|---|
| **PostgreSQL** | Structured, relational data | Records, transactions, reporting |
| **MongoDB** | Flexible, document-based data | Variable schemas, nested content, logs |
| **ChromaDB** | Semantic vector search | Documents, policies, unstructured knowledge |
| **Neo4j** | Relationships and graph traversal | Networks, hierarchies, connected entities |

### Your Scenario Must Answer These Questions

1. **What is the business?** Be specific. Not just "a hospital" but "a regional hospital network that manages patient referrals across 12 specialty clinics."

2. **What structured, relational data does it generate?** This will live in PostgreSQL. Think: records with consistent fields, foreign key relationships, things you would report on.

3. **What document-style data does it generate?** This will live in MongoDB. Think: data that varies in shape from record to record, nested objects, logs, or anything that would be painful to force into a fixed table schema.

4. **What knowledge base does it need to search semantically?** This will live in ChromaDB. Think: policy documents, manuals, FAQs, research, anything where a user might ask a natural-language question and expect a relevant passage back.

5. **What relationships matter in this business?** This will live in Neo4j. Think: who knows whom, what connects to what, supply chains, org charts, influence networks — anything where the *connection itself* carries meaning.

### Example Scenarios

The following are illustrative examples only. Your team should invent an original scenario.

**Hospital Referral Network**
- PostgreSQL: patients, appointments, billing records, insurance
- MongoDB: physician notes, lab results (variable structure per test type)
- ChromaDB: clinical guidelines, drug interaction documents, hospital policies
- Neo4j: patient → referring doctor → specialist → treatment pathway

**E-Commerce Platform**
- PostgreSQL: products, orders, customers, inventory levels
- MongoDB: product reviews, user behavior logs, support tickets
- ChromaDB: product manuals, return policies, FAQ content
- Neo4j: customer → purchased → product → frequently bought with → product

**University Research Administration**
- PostgreSQL: grants, budgets, faculty records, compliance deadlines
- MongoDB: research proposals (variable structure per department)
- ChromaDB: funding agency guidelines, IRB policies, published abstracts
- Neo4j: faculty → collaborates with → faculty → affiliated with → institution

**Smart City Operations**
- PostgreSQL: infrastructure assets, maintenance schedules, work orders
- MongoDB: IoT sensor readings (variable schema per sensor type)
- ChromaDB: city codes, zoning regulations, emergency response protocols
- Neo4j: asset → depends on → asset → maintained by → contractor

---

## Step 2 — Plan Your Data

Once your scenario is defined, plan the actual data your application will use. You do not need massive datasets — **quality and relevance matter more than volume**.

### PostgreSQL
- Define at least **2 related tables** with a foreign key relationship
- Each table should have at least 10 sample rows
- Write out your schema before building

### MongoDB
- Define at least **1 collection** with at least 10 documents
- At least some documents should have different fields to demonstrate the flexible schema advantage

### ChromaDB
- Prepare at least **3 to 5 documents** (PDF, TXT, or Markdown) that represent your knowledge base
- These will be uploaded through the application UI and embedded into the vector store

### Neo4j
- Define at least **2 node types** and **1 relationship type**
- Populate at least 10 nodes and 10 relationships
- Your graph should be queryable in a way that produces meaningful business insight

---

## Step 3 — Build the Application

Your team will build a **single `app.py`** file using Streamlit. The application will be structured as five tabs.

### Project Structure

```
INFO5707/
├── rag_lab_1_postgre/         ← reference only, do not modify
├── rag_lab_2_mongo/           ← reference only, do not modify
├── rag_lab_3_chromadb/        ← reference only, do not modify
├── rag_lab_4_neo4j/           ← reference only, do not modify
├── app.py                     ← your unified application
├── pyproject.toml             ← UV dependency management
├── uv.lock                    ← auto-generated, commit this
├── .env                       ← your credentials, never commit
└── .env.example               ← credential template, commit this
```

### Environment Setup

Your `.env` file should contain credentials for all four databases plus your Groq API key:

```
# PostgreSQL
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=

# MongoDB
MONGO_URI=

# ChromaDB
CHROMA_PERSIST_PATH=./chroma_db

# Neo4j
NEO4J_URI=
NEO4J_USER=
NEO4J_PASSWORD=

# Groq
GROQ_API_KEY=
```

### The Five Tabs

**Tab 1 — PostgreSQL**

This tab is your structured data workbench.
- Enter a natural language question
- Groq translates it to a SQL query and executes it
- Results display as a table
- The generated SQL is shown so you can inspect and learn from it
- A schema viewer shows your tables and column definitions

**Tab 2 — MongoDB**

This tab is your document data workbench.
- Enter a natural language question
- Groq translates it to a MongoDB query and executes it
- Results display as formatted JSON
- The generated query is shown alongside the results
- A collection browser lets you inspect documents

**Tab 3 — ChromaDB**

This tab has two modes, toggled by a radio button.

*Ingest Mode:*
- Upload one or more files (PDF, TXT, Markdown)
- Set chunk size using a slider
- Click to embed and store in the vector database
- Status feedback confirms successful ingestion
- A stats panel shows document count and last ingestion time

*Query Mode:*
- Enter a natural language question
- Returns the top matching chunks with similarity scores and source file names
- Groq synthesizes a response from the retrieved context

**Tab 4 — Neo4j**

This tab has two modes, toggled by a radio button.

*Load Mode:*
- A structured form or CSV uploader to create nodes and relationships
- Designed around your team's specific node and relationship types

*Explore Mode:*
- Enter a natural language question about your graph
- Groq translates it to a Cypher query and executes it
- Results display as a formatted list or table
- The generated Cypher is shown so you can see how the translation works
- A simple path display shows relationships visually as text (e.g., A → relates to → B)

**Tab 5 — Ask Anything**

This is the capstone tab that ties the whole system together.
- Enter any question related to your business scenario
- Groq reads the question and determines which database(s) to query
- Each relevant database is queried and results are retrieved
- Groq synthesizes a unified response from all sources
- A **reasoning trace panel** shows which databases were consulted and why — this is the most important learning artifact in the entire application

### The Sidebar

The sidebar is always visible and contains:
- Your team name and business scenario title
- A **connection health panel** with green/red status indicators for all four databases
- Connection error messages if any database is unreachable

---

## Step 4 — Architecture Document

Your team must commit an `architecture.md` file to your repository. It should address:

1. **Business Scenario** — describe your scenario in 2 to 3 paragraphs
2. **Database Justification** — for each of the four databases, explain specifically why that database is the right tool for your use case, not just what data you stored
3. **Data Model** — your PostgreSQL schema, MongoDB document structure, ChromaDB document list, and Neo4j node/relationship types
4. **System Diagram** — a simple text or image diagram showing how data flows through the application
5. **Team Roles** — who owned which part of the build

---

## Deliverables

| Deliverable | Details |
|---|---|
| Working `app.py` | All five tabs functional, all four databases connected |
| `pyproject.toml` | Complete and tested with UV |
| `.env.example` | All required keys listed, no actual credentials |
| `architecture.md` | Complete, committed to repo |
| GitHub repository | At least one team member's public repo |
| Demo presentation | Live in-class walkthrough of all five tabs |

---

## Grading Emphasis

Your grade will reflect not just whether the application works, but whether your team can explain *why* each architectural decision was made. During the demo you should be prepared to answer:

- Why did this piece of data belong in PostgreSQL and not MongoDB?
- What would break if you tried to use ChromaDB for the data you put in Neo4j?
- What does the Ask Anything tab's reasoning trace tell you about how the system made its decision?

The goal is not a perfect application. The goal is a defensible one.

---

## Getting Help

- The four lab folders in `INFO5707/` remain intact as reference implementations
- Review each lab's `app.py` before building your unified module for that database
- Your instructor will provide a Claude Code markdown briefing document to assist with code generation
- Use that briefing as a starting point, not a finished product — your team is responsible for adapting it to your scenario

---

*INFO5707 — Data Modeling | Capstone Project*
