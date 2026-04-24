# Team Architecture Document
## INFO5707 — Data Modeling | RAG Capstone

**Team Name:**
**Team Members:**
**Business Scenario Title:**
**Date:**

---

> **Instructions:** Complete every section of this document before your demo. This is not a formality — your ability to explain and defend these decisions is part of your grade. Incomplete sections will be noted during the demo. Delete all instructional text (shown in italics) before submitting.

---

## Section 1 — Business Scenario

### 1.1 Scenario Description

*Describe your business scenario in 2 to 3 bullet points. Be specific — name the organization, what it does, and what operational challenge the application addresses.*

-
-
-

### 1.2 The Business Problem

*What question or problem does this application help solve? What would a real employee or analyst use this system for day to day?*

-
-

### 1.3 Why Four Databases Are Required

*In one bullet per database, explain why this scenario genuinely needs that database type — not just that you used it because the assignment required it.*

- **PostgreSQL:**
- **MongoDB:**
- **ChromaDB:**
- **Neo4j:**

---

## Section 2 — Data Model

### 2.1 PostgreSQL Schema

*List every table you created, its columns, data types, and any constraints or relationships. Use the format below.*

**Table: `[table_name]`**

| Column | Data Type | Constraints | Notes |
|---|---|---|---|
| | | | |

**Table: `[table_name]`**

| Column | Data Type | Constraints | Notes |
|---|---|---|---|
| | | | |

*Describe the foreign key relationship(s) between your tables:*
-

*Why did this data belong in PostgreSQL and not MongoDB?*
-

### 2.2 MongoDB Collections

*Describe each collection and the document structure. Show at least one example document per collection.*

**Collection: `[collection_name]`**

*Purpose:*

*Example document:*
```json
{

}
```

*What fields vary between documents in this collection, and why is that variation meaningful?*
-

*Why did this data belong in MongoDB and not PostgreSQL?*
-

### 2.3 ChromaDB Knowledge Base

*List every document you ingested into ChromaDB. For each one, describe what it contains and what kinds of questions it helps answer.*

| Document Name | Content Description | Example Question It Answers |
|---|---|---|
| | | |
| | | |
| | | |

*What chunk size did your team use, and why?*
-

*Why did this content belong in ChromaDB and not in MongoDB or PostgreSQL?*
-

### 2.4 Neo4j Graph Model

*Describe your node types, relationship types, and the properties on each.*

**Node Labels:**

| Label | Properties | Description |
|---|---|---|
| | | |
| | | |

**Relationship Types:**

| Type | From Node | To Node | Properties | Description |
|---|---|---|---|---|
| | | | | |

*Draw a simple ASCII diagram of your graph model:*

```
(NodeLabel) -[:RELATIONSHIP]-> (NodeLabel)
```

*What question can be answered by traversing your graph that could NOT be answered efficiently with a SQL join?*
-

*Why did this data belong in Neo4j and not PostgreSQL?*
-

---

## Section 3 — Database Justification Summary

*Complete this table. For each database, state what specific data you stored and provide a one-sentence justification for that choice.*

| Database | Data Stored | Justification for This Choice |
|---|---|---|
| PostgreSQL | | |
| MongoDB | | |
| ChromaDB | | |
| Neo4j | | |

---

## Section 4 — LLM Integration

### 4.1 Query Translation

*For each database, describe an example natural language question your app handles and the query it generates.*

**PostgreSQL**
- Question:
- Generated SQL:

**MongoDB**
- Question:
- Generated query:

**ChromaDB**
- Question:
- Retrieved source document(s):

**Neo4j**
- Question:
- Generated Cypher:

### 4.2 Ask Anything — Routing Example

*Describe one question you tested in the Ask Anything tab. Fill in what the routing trace showed.*

- Question asked:
- Databases selected by Groq:
- Routing reasoning displayed:
- Quality of synthesised answer (good / partial / poor) and why:

### 4.3 Prompt Engineering Observations

*What did your team observe about how prompt quality affected query generation? Did you have to adjust any prompts? What did you change and why?*

-
-

---

## Section 5 — System Diagram

*Provide a simple diagram showing how data flows through your application for a typical user query. ASCII art, a drawn image, or a tool-generated diagram are all acceptable.*

```
[User Question]
      │
      ▼
[Your diagram here]
      │
      ▼
[Answer displayed in UI]
```

---

## Section 6 — Challenges and Decisions

### 6.1 Most Difficult Technical Challenge

*What was the hardest technical problem your team encountered? How did you resolve it?*

-
-

### 6.2 A Decision You Would Make Differently

*If you were starting over, what one data modeling or architectural decision would you change? Why?*

-

### 6.3 What Surprised You

*What was something about one of the four database types that surprised your team during this project?*

-

---

## Section 7 — Team Roles

*Document who owned which part of the build. Every team member should be able to speak to every part during the demo, but ownership should be clear.*

| Team Member | Primary Responsibility | Secondary Contribution |
|---|---|---|
| | | |
| | | |
| | | |
| | | |
| | | |

---

## Section 8 — Demo Preparation

*List three questions you expect the instructor to ask during your demo, and your prepared answers.*

**Question 1:**
- Answer:

**Question 2:**
- Answer:

**Question 3:**
- Answer:

---

## Section 9 — Deliverable Checklist

*Check every item before submitting. Do not submit with unchecked boxes.*

- [ ] `app.py` — all five tabs functional
- [ ] All four databases connected and showing green in sidebar
- [ ] PostgreSQL tab — schema viewer works, SQL displayed with results
- [ ] MongoDB tab — collection selector works, query displayed with results
- [ ] ChromaDB tab — at least 3 documents ingested, semantic search returns relevant results
- [ ] Neo4j tab — nodes and relationships loaded, Cypher displayed with results
- [ ] Ask Anything tab — routing trace visible, synthesised answer displayed
- [ ] `pyproject.toml` — complete, `uv sync` runs without errors
- [ ] `.env.example` — all keys present, no actual credentials
- [ ] `architecture.md` — this document, fully completed
- [ ] GitHub repository — at least one team member's public repo with final code
- [ ] All instructional italicised text removed from this document

---

*INFO5707 — Data Modeling | Team Architecture Template v1.0*
