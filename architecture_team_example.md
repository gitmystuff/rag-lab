# Team Architecture Document — EXAMPLE
## INFO5707 — Data Modeling | RAG Capstone

**Team Name:** Team Healthbridge
**Team Members:** Alice Morgan, Ben Okafor, Carmen Liu, David Park
**Business Scenario Title:** Regional Hospital Referral Network
**Date:** Spring 2026

---

> **NOTE TO STUDENTS:** This is a completed example document showing the level of detail expected. Your scenario, data models, and justifications must be original to your team. Do not copy this example.

---

## Section 1 — Business Scenario

### 1.1 Scenario Description

- A regional hospital network manages patient care across 12 specialty clinics spread across three counties
- Physicians refer patients between clinics, and care coordinators need to track referral pathways, access clinical notes, search treatment guidelines, and understand which specialists are most connected in the referral network
- The application serves as an operational intelligence layer for care coordinators and hospital administrators

### 1.2 The Business Problem

- Care coordinators currently use three separate systems to track patient records, clinical notes, and referral history — this application unifies them under a single natural language interface
- Administrators need to identify bottlenecks in the referral network (e.g., a specialist with too many incoming referrals and no outgoing ones) — a question that is easy in a graph but painful in SQL

### 1.3 Why Four Databases Are Required

- **PostgreSQL:** Patient demographics, appointments, and billing records are structured, consistent, and require transactional integrity — the exact use case for a relational model
- **MongoDB:** Physician clinical notes vary significantly in structure depending on the type of visit and specialty — forcing them into a fixed schema would lose important detail
- **ChromaDB:** Clinical guidelines, drug interaction documents, and hospital policies are unstructured text that care coordinators need to search semantically — keyword search alone is insufficient
- **Neo4j:** The referral network is fundamentally a graph — patients, physicians, and clinics are nodes; referrals are directed relationships; the interesting questions are all about traversal

---

## Section 2 — Data Model

### 2.1 PostgreSQL Schema

**Table: `patients`**

| Column | Data Type | Constraints | Notes |
|---|---|---|---|
| patient_id | SERIAL | PRIMARY KEY | Auto-incrementing |
| first_name | VARCHAR(100) | NOT NULL | |
| last_name | VARCHAR(100) | NOT NULL | |
| date_of_birth | DATE | NOT NULL | |
| insurance_id | VARCHAR(50) | UNIQUE | |
| primary_physician_id | INTEGER | FK → physicians.physician_id | |

**Table: `physicians`**

| Column | Data Type | Constraints | Notes |
|---|---|---|---|
| physician_id | SERIAL | PRIMARY KEY | |
| full_name | VARCHAR(150) | NOT NULL | |
| specialty | VARCHAR(100) | NOT NULL | |
| clinic_id | INTEGER | FK → clinics.clinic_id | |

**Table: `appointments`**

| Column | Data Type | Constraints | Notes |
|---|---|---|---|
| appointment_id | SERIAL | PRIMARY KEY | |
| patient_id | INTEGER | FK → patients.patient_id | |
| physician_id | INTEGER | FK → physicians.physician_id | |
| appointment_date | TIMESTAMP | NOT NULL | |
| status | VARCHAR(20) | CHECK (IN ('scheduled','completed','cancelled')) | |

- `appointments.patient_id` references `patients.patient_id` — one patient, many appointments
- `appointments.physician_id` references `physicians.physician_id` — one physician, many appointments
- `patients.primary_physician_id` references `physicians.physician_id` — each patient has one primary physician

*Why this data belongs in PostgreSQL and not MongoDB:*
- Patient and appointment records have a fixed, well-known structure that never varies
- Referential integrity between patients, physicians, and appointments is enforced at the database level
- Billing and compliance reporting requires reliable aggregation over consistent columns — something relational databases are optimized for

### 2.2 MongoDB Collections

**Collection: `clinical_notes`**

*Purpose:* Stores physician notes from patient visits. Structure varies by specialty — a cardiology note has different fields than a dermatology note.

*Example document (cardiology):*
```json
{
  "patient_id": 1042,
  "physician_id": 7,
  "visit_date": "2026-03-15",
  "specialty": "cardiology",
  "chief_complaint": "Chest pain on exertion",
  "vitals": {
    "bp_systolic": 145,
    "bp_diastolic": 92,
    "heart_rate": 88
  },
  "ecg_findings": "Sinus rhythm with left bundle branch block",
  "medications_adjusted": ["metoprolol increased to 100mg"],
  "follow_up_weeks": 4
}
```

*Example document (dermatology):*
```json
{
  "patient_id": 887,
  "physician_id": 14,
  "visit_date": "2026-03-18",
  "specialty": "dermatology",
  "chief_complaint": "Persistent rash on left forearm",
  "lesion_description": "Erythematous plaques, 3cm diameter",
  "biopsy_taken": true,
  "biopsy_result": "Pending",
  "treatment": "Triamcinolone cream 0.1% applied twice daily"
}
```

*Field variation:* Cardiology notes include `vitals`, `ecg_findings`, and `medications_adjusted`; dermatology notes include `lesion_description` and `biopsy_taken`. Forcing both into a single relational schema would require many nullable columns or a complex subtype design.

*Why this data belongs in MongoDB and not PostgreSQL:*
- The document structure changes fundamentally between specialties — not just the values, but the fields themselves
- Adding a new specialty requires no schema migration, only a new document shape
- Embedding nested vitals and findings in a single document reflects how physicians actually think about a note — as a whole, not as rows across multiple tables

### 2.3 ChromaDB Knowledge Base

| Document Name | Content Description | Example Question It Answers |
|---|---|---|
| `ACC_Heart_Failure_Guidelines_2024.pdf` | AHA/ACC clinical guidelines for heart failure management | What is the recommended first-line treatment for HFrEF? |
| `drug_interactions_formulary.txt` | Hospital formulary with known drug interaction warnings | Can metoprolol and diltiazem be co-administered? |
| `referral_policy_v3.md` | Hospital policy for inter-clinic referral procedures and required documentation | What documentation is required before referring a patient to a specialist? |
| `HIPAA_patient_rights.txt` | Patient rights documentation under HIPAA | What are a patient's rights regarding access to their medical records? |
| `discharge_planning_protocol.md` | Step-by-step discharge planning checklist for care coordinators | What steps must be completed before a patient can be discharged? |

*Chunk size used:* 512 characters with 50-character overlap. This was chosen because clinical guidelines have dense information per paragraph — smaller chunks lost context; larger chunks returned too much irrelevant content in retrieval.

*Why this content belongs in ChromaDB and not MongoDB or PostgreSQL:*
- These are reference documents, not operational records — they are read, not written to
- Care coordinators ask questions in natural language; keyword search would miss synonyms and related concepts
- The content is unstructured prose — forcing it into rows or documents would destroy the semantic relationships between sentences

### 2.4 Neo4j Graph Model

**Node Labels:**

| Label | Properties | Description |
|---|---|---|
| `:Patient` | patient_id, name, age | A patient in the network |
| `:Physician` | physician_id, name, specialty | A physician at a clinic |
| `:Clinic` | clinic_id, name, county | A clinic in the network |

**Relationship Types:**

| Type | From Node | To Node | Properties | Description |
|---|---|---|---|---|
| `:REFERRED_TO` | `:Physician` | `:Physician` | date, reason, patient_id | One physician referred a patient to another |
| `:TREATED_AT` | `:Patient` | `:Clinic` | first_visit, visit_count | A patient receives care at a clinic |
| `:WORKS_AT` | `:Physician` | `:Clinic` | since_year | A physician is affiliated with a clinic |

*ASCII graph diagram:*

```
(:Patient)-[:TREATED_AT]->(:Clinic)<-[:WORKS_AT]-(:Physician)
                                                        │
                                                [:REFERRED_TO]
                                                        │
                                                        ▼
                                                  (:Physician)
```

*Question answerable by graph traversal but not efficiently by SQL:*
- "Which physicians are within two referral hops of Dr. Chen, and what specialties do they cover?"
- In SQL this requires a recursive CTE or multiple self-joins on a referrals table; in Cypher it is: `MATCH (p:Physician {name: 'Dr. Chen'})-[:REFERRED_TO*1..2]->(other:Physician) RETURN other.name, other.specialty`

*Why this data belongs in Neo4j and not PostgreSQL:*
- The referral network is not just data — it is a structure of connections, and the structure is what we query
- SQL can represent a referral table, but multi-hop traversal requires recursive queries that are complex to write and slow to execute at scale
- Graph algorithms like PageRank on the referral network (who is the most influential referrer) are native to Neo4j and impractical in SQL

---

## Section 3 — Database Justification Summary

| Database | Data Stored | Justification for This Choice |
|---|---|---|
| PostgreSQL | Patients, physicians, appointments, clinics | Fixed schema, referential integrity, and aggregate reporting requirements make this the only appropriate model |
| MongoDB | Clinical notes by specialty | Variable document structure per specialty eliminates the need for complex nullable-column schema designs |
| ChromaDB | Clinical guidelines, drug formulary, hospital policies | Unstructured reference documents require semantic search — exact keyword matching fails for clinical terminology |
| Neo4j | Referral relationships between physicians, patient clinic visits | Multi-hop traversal of the referral network is the core use case; this is a graph problem, not a table problem |

---

## Section 4 — LLM Integration

### 4.1 Query Translation

**PostgreSQL**
- Question: "How many completed appointments did Dr. Chen have in March 2026?"
- Generated SQL: `SELECT COUNT(*) FROM appointments a JOIN physicians p ON a.physician_id = p.physician_id WHERE p.full_name = 'Dr. Chen' AND a.status = 'completed' AND a.appointment_date BETWEEN '2026-03-01' AND '2026-03-31';`

**MongoDB**
- Question: "Show me all cardiology notes where the patient had elevated blood pressure"
- Generated query: `{"specialty": "cardiology", "vitals.bp_systolic": {"$gt": 140}}`

**ChromaDB**
- Question: "What is the first-line treatment for heart failure with reduced ejection fraction?"
- Retrieved source: `ACC_Heart_Failure_Guidelines_2024.pdf` — chunk describing ACE inhibitor and beta-blocker therapy

**Neo4j**
- Question: "Which physicians has Dr. Patel referred patients to in the last 6 months?"
- Generated Cypher: `MATCH (p:Physician {name: 'Dr. Patel'})-[r:REFERRED_TO]->(other:Physician) WHERE r.date >= date() - duration({months: 6}) RETURN other.name, other.specialty, count(r) AS referral_count ORDER BY referral_count DESC`

### 4.2 Ask Anything — Routing Example

- Question asked: "What do we know about patient 1042's care history and which guidelines are relevant to their condition?"
- Databases selected by Groq: PostgreSQL, MongoDB, ChromaDB
- Routing reasoning: "Patient history is in PostgreSQL, clinical notes in MongoDB, and relevant treatment guidelines in ChromaDB. Neo4j is not needed as the question is about a single patient's records, not network relationships."
- Quality of synthesised answer: Good — Groq correctly identified that Neo4j was not needed and produced a coherent summary combining appointment history, cardiology notes, and heart failure guideline excerpts

### 4.3 Prompt Engineering Observations

- The MongoDB query generator initially produced queries with field names that did not match our actual documents — we fixed this by increasing the sample size from 2 to 5 documents in the prompt
- The Neo4j Cypher generator failed on date arithmetic until we added an example of Neo4j date syntax to the schema prompt
- The Ask Anything router occasionally included Neo4j for questions that were clearly about individual records — adding "Neo4j is appropriate only when the question is about relationships or connections between multiple entities" to the routing prompt fixed this

---

## Section 5 — System Diagram

```
[Care Coordinator enters question]
            │
            ▼
    [Ask Anything Tab]
            │
            ▼
    [Groq — Routing LLM]
    "Which DBs are relevant?"
      │         │         │
      ▼         ▼         ▼
[PostgreSQL] [MongoDB] [ChromaDB]
 Appointments  Clinical  Guidelines
   & Records    Notes    & Policies
      │         │         │
      └────┬────┘         │
           ▼              │
   [Groq — Synthesis LLM] ◄──┘
   "Combine all results into
    one coherent answer"
           │
           ▼
   [Reasoning Trace + Answer
    displayed in Streamlit UI]
```

---

## Section 6 — Challenges and Decisions

### 6.1 Most Difficult Technical Challenge

- The Neo4j date handling was our biggest challenge — Cypher uses `date()` and `duration()` functions differently from SQL's `DATEADD`, and Groq's training data had more SQL examples than Cypher
- We resolved it by adding explicit Cypher date examples to the schema injection prompt in `nl_to_cypher()`

### 6.2 A Decision You Would Make Differently

- We stored `clinic_id` in both the `physicians` PostgreSQL table and as a Neo4j node property, creating a sync problem when we updated clinic names
- We would store clinic data only in Neo4j and reference it by ID in PostgreSQL, with a join at query time — the duplication was unnecessary and caused confusion

### 6.3 What Surprised Your Team

- We were surprised that ChromaDB returned relevant results even when the user's question used different terminology than the documents — asking about "ejection fraction issues" returned the heart failure guideline even though it never uses that exact phrase
- This made the value of semantic search immediately concrete in a way that a textbook definition never would have

---

## Section 7 — Team Roles

| Team Member | Primary Responsibility | Secondary Contribution |
|---|---|---|
| Alice Morgan | PostgreSQL schema design and Tab 1 | Ask Anything routing prompt tuning |
| Ben Okafor | MongoDB collection design and Tab 2 | Architecture document |
| Carmen Liu | ChromaDB ingestion pipeline and Tab 3 | Document selection and chunking strategy |
| David Park | Neo4j graph model design and Tab 4 | Neo4j Cypher prompt engineering |

---

## Section 8 — Demo Preparation

**Question 1:** Why did you use MongoDB for clinical notes instead of adding more tables to PostgreSQL?
- Answer: Each medical specialty produces structurally different notes — cardiology notes have vitals and ECG fields that dermatology notes don't have and never will. In PostgreSQL we would need either a wide table with many nullable columns or a complex subtype design. MongoDB lets each specialty's notes have exactly the fields they need without affecting other specialties.

**Question 2:** What would break if you tried to put your Neo4j data in PostgreSQL?
- Answer: The referral network traversal queries would require recursive CTEs. The question "which physicians are within two referral hops of Dr. Patel" is one line of Cypher; in SQL it requires a WITH RECURSIVE query that is error-prone and slow on large datasets. Graph algorithms like PageRank on the referral network are not available in PostgreSQL at all.

**Question 3:** How does the Ask Anything tab know which databases to query?
- Answer: We send the question to Groq with a description of each database's role and ask it to return a JSON list of which databases are relevant. Groq then explains its reasoning, which appears in the reasoning trace panel. The app queries only the selected databases and sends all results back to Groq for synthesis into a final answer.

---

## Section 9 — Deliverable Checklist

- [x] `app.py` — all five tabs functional
- [x] All four databases connected and showing green in sidebar
- [x] PostgreSQL tab — schema viewer works, SQL displayed with results
- [x] MongoDB tab — collection selector works, query displayed with results
- [x] ChromaDB tab — 5 documents ingested, semantic search returns relevant results
- [x] Neo4j tab — nodes and relationships loaded, Cypher displayed with results
- [x] Ask Anything tab — routing trace visible, synthesised answer displayed
- [x] `pyproject.toml` — complete, `uv sync` runs without errors
- [x] `.env.example` — all keys present, no actual credentials
- [x] `architecture.md` — this document, fully completed
- [x] GitHub repository — public repo with final code
- [x] All instructional italicised text removed from this document

---

*INFO5707 — Data Modeling | Team Architecture Example — Team Healthbridge*
