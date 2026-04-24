"""
app.py
======
Unified Multi-Database RAG Capstone
INFO5707 — Data Modeling

Databases: PostgreSQL · MongoDB · ChromaDB · Neo4j
LLM:       Groq (llama-3.1-8b-instant)
UI:        Streamlit

Sections:
  1.  IMPORTS
  2.  CONFIGURATION
  3.  DATABASE CONNECTIONS
  4.  CONNECTION HEALTH CHECK
  5.  POSTGRESQL MODULE
  6.  MONGODB MODULE
  7.  CHROMADB MODULE
  8.  NEO4J MODULE
  9.  LANGGRAPH AGENT (ChromaDB)
  10. ASK ANYTHING ROUTER
  11. STREAMLIT UI

Run with:
    uv run streamlit run app.py
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────────────────

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Annotated

import chromadb
import pandas as pd
import psycopg2
import psycopg2.extras
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from neo4j import GraphDatabase
from pymongo import MongoClient
from typing_extensions import TypedDict

load_dotenv()

# ── 2. CONFIGURATION ──────────────────────────────────────────────────────────

# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_PROVIDER    = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── POSTGRESQL ───────────────────────────────────────────────────────────────
PG_HOST     = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT     = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB       = os.getenv("POSTGRES_DB", "")
PG_USER     = os.getenv("POSTGRES_USER", "")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# ── MONGODB ──────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "")

# ── CHROMADB ─────────────────────────────────────────────────────────────────
CHROMA_PERSIST_PATH  = os.getenv("CHROMA_PERSIST_PATH", "./chroma_db")
CHROMA_COLLECTION    = os.getenv("CHROMA_COLLECTION", "rag_capstone")
EMBEDDING_MODEL      = "all-MiniLM-L6-v2"
CHUNK_SIZE           = 512
CHUNK_OVERLAP        = 50
RETRIEVAL_K          = 4
SIMILARITY_THRESHOLD = 0.3

# ── NEO4J ────────────────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# ── 3. DATABASE CONNECTIONS ───────────────────────────────────────────────────

@st.cache_resource
def get_postgres_conn():
    """
    Establish and cache a PostgreSQL connection.

    Teaching note: connect_timeout=5 prevents the app from hanging
    for the default 30+ seconds if the host is unreachable. In a
    classroom setting, fast failure is essential for debugging.
    Returns None if connection fails — callers must check before use.
    """
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD,
            connect_timeout=5,
        )
        return conn
    except Exception:
        return None


@st.cache_resource
def get_mongo_db():
    """
    Establish and cache a MongoDB database handle.

    Teaching note: MongoClient is lazy — it does not actually connect
    until the first operation. We force an immediate check using
    server_info() so the health panel reflects true connection status.
    Returns None if connection fails.
    """
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()   # force connection attempt
        return client[MONGO_DB]
    except Exception:
        return None


@st.cache_resource
def get_chroma_collection():
    """
    Initialize and cache the persistent ChromaDB collection.

    Teaching note: PersistentClient saves data to disk at
    CHROMA_PERSIST_PATH. The collection survives restarts — documents
    ingested in one session are available in the next.
    ChromaDB is local-only so connection failure is rare, but we still
    wrap it for consistency with the other modules.
    """
    try:
        Path(CHROMA_PERSIST_PATH).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
        collection = client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        return collection
    except Exception:
        return None


@st.cache_resource
def get_neo4j_driver():
    """
    Establish and cache a Neo4j driver instance.

    Teaching note: the Neo4j driver maintains a connection pool.
    verify_connectivity() tests the connection immediately. The driver
    must be closed on app shutdown, but for a classroom Streamlit app
    the process lifecycle handles this naturally.
    Returns None if connection fails.
    """
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        return driver
    except Exception:
        return None


# ── 4. CONNECTION HEALTH CHECK ────────────────────────────────────────────────

def check_all_connections() -> dict:
    """
    Attempt all four database connections and return a status dict.

    Returns:
        dict with keys: postgres, mongo, chroma, neo4j
        Each value is a dict: {"ok": bool, "message": str}

    Teaching note: this is called once on app load and again when
    the user clicks Retry. Results drive the sidebar health panel.
    """
    status = {}

    # PostgreSQL
    conn = get_postgres_conn()
    if conn is not None:
        try:
            conn.cursor().execute("SELECT 1")
            status["postgres"] = {"ok": True,  "message": "Connected"}
        except Exception as e:
            status["postgres"] = {"ok": False, "message": str(e)}
    else:
        status["postgres"] = {"ok": False, "message": "Could not connect — check .env credentials"}

    # MongoDB
    db = get_mongo_db()
    status["mongo"] = (
        {"ok": True,  "message": "Connected"}
        if db is not None
        else {"ok": False, "message": "Could not connect — check MONGO_URI in .env"}
    )

    # ChromaDB
    col = get_chroma_collection()
    status["chroma"] = (
        {"ok": True,  "message": f"Connected — {col.count()} chunks"}
        if col is not None
        else {"ok": False, "message": "Could not initialize local ChromaDB"}
    )

    # Neo4j
    driver = get_neo4j_driver()
    status["neo4j"] = (
        {"ok": True,  "message": "Connected"}
        if driver is not None
        else {"ok": False, "message": "Could not connect — check NEO4J_URI and password in .env"}
    )

    return status


# ── 5. POSTGRESQL MODULE ──────────────────────────────────────────────────────

@st.cache_resource
def get_llm():
    """
    Load and cache the LLM based on LLM_PROVIDER config.

    Teaching note: both ChatGroq and ChatOllama implement the same
    LangChain BaseChatModel interface. Switching providers requires
    only changing LLM_PROVIDER in .env — no downstream code changes.
    This is the strategy pattern in practice.
    """
    if LLM_PROVIDER == "ollama":
        return ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    return ChatGroq(api_key=GROQ_API_KEY, model_name=GROQ_MODEL)


def get_postgres_schema() -> str:
    """
    Retrieve table and column definitions from the connected database.

    Queries information_schema to build a schema string that Groq
    uses as context when generating SQL.

    Teaching note: giving the LLM the actual schema — not a hardcoded
    description — means this function works for any team's database
    without code changes. The schema is the prompt.
    """
    conn = get_postgres_conn()
    if conn is None:
        return ""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        rows = cursor.fetchall()
        if not rows:
            return "No tables found in the public schema."
        schema_lines = []
        current_table = None
        for table, column, dtype in rows:
            if table != current_table:
                schema_lines.append(f"\nTable: {table}")
                current_table = table
            schema_lines.append(f"  - {column} ({dtype})")
        return "\n".join(schema_lines)
    except Exception as e:
        return f"Schema retrieval error: {e}"


def nl_to_sql(question: str, schema: str) -> str:
    """
    Use Groq to translate a natural language question into SQL.

    Teaching note: the schema string is injected directly into the
    prompt. The LLM has no knowledge of the database otherwise.
    This is prompt engineering as schema-aware translation.
    """
    llm = get_llm()
    prompt = f"""You are a PostgreSQL expert. Convert the question below into a valid SQL query.

Database schema:
{schema}

Rules:
- Return ONLY the SQL query, no explanation, no markdown, no backticks.
- Use only tables and columns that exist in the schema above.
- If the question cannot be answered from the schema, return: SELECT 'Cannot answer from available schema' AS message;

Question: {question}

SQL:"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def run_postgres_query(sql: str) -> tuple[list, list]:
    """
    Execute a SQL query and return (rows, column_names).

    Teaching note: RealDictCursor returns rows as dicts, which makes
    it easier to build a DataFrame. We explicitly rollback on error
    to keep the connection in a usable state for the next query.
    """
    conn = get_postgres_conn()
    if conn is None:
        return [], []
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return rows, columns
    except Exception as e:
        conn.rollback()
        raise e


# ── 6. MONGODB MODULE ─────────────────────────────────────────────────────────

def get_mongo_collections() -> list[str]:
    """Return a list of collection names in the connected database."""
    db = get_mongo_db()
    if db is None:
        return []
    try:
        return db.list_collection_names()
    except Exception:
        return []


def get_collection_sample(collection_name: str, limit: int = 3) -> list:
    """
    Return a sample of documents from a collection.

    Teaching note: we convert ObjectId to string here so the documents
    can be serialised to JSON for display. ObjectId is not JSON-
    serialisable by default — this is a common gotcha with MongoDB
    in Python.
    """
    db = get_mongo_db()
    if db is None:
        return []
    try:
        docs = list(db[collection_name].find({}, {"_id": 0}).limit(limit))
        return docs
    except Exception:
        return []


def nl_to_mongo_query(question: str, collection_name: str, sample_docs: list) -> str:
    """
    Use Groq to translate a natural language question into a MongoDB
    query expressed as a Python dict (for use with find() or aggregate()).

    Teaching note: we show the LLM a sample of real documents from the
    collection so it knows the actual field names and value types.
    This is few-shot prompting using real data instead of invented examples.
    """
    llm = get_llm()
    sample_str = str(sample_docs[:2]) if sample_docs else "No sample available"
    prompt = f"""You are a MongoDB expert. Convert the question below into a MongoDB query.

Collection: {collection_name}
Sample documents: {sample_str}

Rules:
- Return ONLY a valid Python dict for use with collection.find() or collection.aggregate().
- No explanation, no markdown, no backticks, no variable names.
- If aggregation is needed, return a Python list of pipeline stage dicts.
- If the question cannot be answered, return: {{"error": "Cannot answer from available data"}}

Question: {question}

Query:"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def run_mongo_query(collection_name: str, query_str: str) -> list:
    """
    Execute a MongoDB query string (returned by Groq) against a collection.

    Teaching note: eval() is used here in a controlled classroom context
    to execute the query string returned by the LLM. In a production
    system you would parse and validate the query before executing it.
    This is an intentional teaching moment about the risks of executing
    LLM-generated code without validation.
    """
    db = get_mongo_db()
    if db is None:
        return []
    try:
        query = eval(query_str)  # noqa: S307 — intentional, classroom context
        collection = db[collection_name]
        if isinstance(query, list):
            results = list(collection.aggregate(query))
        else:
            results = list(collection.find(query, {"_id": 0}).limit(50))
        return results
    except Exception as e:
        raise e


# ── 7. CHROMADB MODULE ────────────────────────────────────────────────────────

@st.cache_resource
def get_embedding_model():
    """
    Load and cache the sentence-transformers embedding model.

    Teaching note: @st.cache_resource means this runs ONCE per
    application session, not on every Streamlit rerun. Without this,
    the 90MB model would reload on every button click.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
        show_progress=True,
    )


def generate_doc_id(filename: str, content: str) -> str:
    """
    Generate a deterministic document ID from filename and content.

    Teaching note: using a content hash means uploading the same file
    twice always produces the same ID. This is the foundation of
    duplicate detection — content-addressed storage.
    """
    return hashlib.sha256(f"{filename}::{content[:500]}".encode()).hexdigest()[:16]


def load_file(uploaded_file) -> list:
    """
    Load an uploaded Streamlit file into LangChain Documents.

    Supports PDF, Markdown (.md), and plain text (.txt).
    Saves the uploaded file to a temp directory first because
    LangChain loaders expect a file path, not a file object.
    """
    suffix = Path(uploaded_file.name).suffix.lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_path)
        elif suffix == ".md":
            loader = TextLoader(tmp_path)
        elif suffix == ".txt":
            loader = TextLoader(tmp_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        docs = loader.load()

        # Attach the original filename to metadata so citations work
        for doc in docs:
            doc.metadata["source"] = uploaded_file.name

        return docs

    finally:
        os.unlink(tmp_path)  # clean up temp file


def chunk_documents(docs: list) -> list:
    """
    Split loaded documents into smaller chunks for embedding.

    Teaching note: chunk size and overlap are deliberate choices.
    - Too large: retrieval returns too much context, LLM gets confused
    - Too small: individual chunks lack enough context to be useful
    - Overlap: prevents a concept split across a boundary from being lost
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(docs)


def check_duplicate(collection, doc_id: str) -> bool:
    """
    Check whether a document chunk already exists in the collection.

    Teaching note: get() with an ID returns the item if it exists.
    An empty result means the chunk is new. This prevents bloating
    the vector store with duplicate content on re-upload.
    """
    result = collection.get(ids=[doc_id])
    return len(result["ids"]) > 0


def ingest_documents(uploaded_files) -> dict:
    """
    Full ingestion pipeline: load → chunk → embed → store.

    Returns a summary dict with counts of ingested and skipped chunks.

    Teaching note: walk students through this pipeline step by step —
    it is the core of any RAG system. Everything else (retrieval,
    generation) is downstream of ingestion quality.
    """
    collection  = get_chroma_collection()
    embeddings  = get_embedding_model()

    total_ingested = 0
    total_skipped  = 0
    total_errors   = []
    processed_files = []

    for uploaded_file in uploaded_files:
        try:
            # Step 1 — load file into LangChain Documents
            docs = load_file(uploaded_file)

            # Step 2 — split into chunks
            chunks = chunk_documents(docs)

            file_ingested = 0
            file_skipped  = 0

            # Step 3 — embed and store each chunk
            for i, chunk in enumerate(chunks):
                doc_id = generate_doc_id(
                    uploaded_file.name,
                    f"{chunk.page_content}_{i}"
                )

                # Step 4 — duplicate guard
                if check_duplicate(collection, doc_id):
                    file_skipped += 1
                    continue

                # Step 5 — embed the chunk text
                vector = embeddings.embed_documents([chunk.page_content])[0]

                # Step 6 — upsert into ChromaDB
                collection.upsert(
                    ids=[doc_id],
                    embeddings=[vector],
                    documents=[chunk.page_content],
                    metadatas=[{
                        "source": uploaded_file.name,
                        "chunk_index": i,
                    }],
                )
                file_ingested += 1

            total_ingested += file_ingested
            total_skipped  += file_skipped
            processed_files.append(uploaded_file.name)

        except Exception as e:
            total_errors.append(f"{uploaded_file.name}: {str(e)}")

    return {
        "ingested": total_ingested,
        "skipped":  total_skipped,
        "errors":   total_errors,
        "files":    processed_files,
    }


def query_vector_store(query: str) -> list:
    """
    Retrieve the top-k most relevant chunks for a query.

    Filters out chunks below SIMILARITY_THRESHOLD — this is the
    hallucination guard. If nothing relevant exists in the corpus,
    return an empty list rather than low-quality chunks.

    Teaching note: similarity score = 1 - cosine_distance.
    A score of 1.0 = identical. A score of 0.0 = completely unrelated.
    The threshold of 0.3 means "at least somewhat relevant."
    Tune this up to reduce noise, down to retrieve more broadly.
    """
    collection = get_chroma_collection()
    embeddings = get_embedding_model()

    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=RETRIEVAL_K,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    if results["ids"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = 1 - dist  # convert cosine distance to similarity score
            if score >= SIMILARITY_THRESHOLD:
                chunks.append({
                    "text":   doc,
                    "source": meta.get("source", "unknown"),
                    "score":  round(score, 3),
                })

    return chunks


def get_collection_stats() -> dict:
    """Return a summary of the current ChromaDB collection."""
    collection = get_chroma_collection()
    count = collection.count()
    sources = set()
    if count > 0:
        results = collection.get(include=["metadatas"])
        for meta in results["metadatas"]:
            sources.add(meta.get("source", "unknown"))
    return {"total_chunks": count, "sources": sorted(sources)}


# ── 8. NEO4J MODULE ───────────────────────────────────────────────────────────

def get_neo4j_schema() -> str:
    """
    Retrieve node labels, relationship types, and property keys from Neo4j.

    Teaching note: CALL db.schema.visualization() gives a structural
    overview but requires Neo4j Enterprise in some versions. We use
    apoc-free alternatives: db.labels(), db.relationshipTypes(), and
    a sample node query to infer properties. This works on Community
    Edition which is what most students will have.
    """
    driver = get_neo4j_driver()
    if driver is None:
        return ""
    try:
        schema_parts = []
        with driver.session() as session:
            # Node labels
            labels = [r["label"] for r in session.run("CALL db.labels()")]
            schema_parts.append(f"Node labels: {', '.join(labels)}")

            # Relationship types
            rel_types = [r["relationshipType"] for r in session.run("CALL db.relationshipTypes()")]
            schema_parts.append(f"Relationship types: {', '.join(rel_types)}")

            # Sample properties per label
            for label in labels:
                result = session.run(f"MATCH (n:`{label}`) RETURN n LIMIT 1")
                record = result.single()
                if record:
                    props = list(dict(record["n"]).keys())
                    schema_parts.append(f"  {label} properties: {', '.join(props)}")

        return "\n".join(schema_parts)
    except Exception as e:
        return f"Schema retrieval error: {e}"


def nl_to_cypher(question: str, schema: str) -> str:
    """
    Use Groq to translate a natural language question into a Cypher query.

    Teaching note: Cypher generation is harder than SQL generation
    because the schema is a graph — paths and relationships matter,
    not just columns. Giving Groq the labels, relationship types, and
    property names is essential for producing valid queries.
    """
    llm = get_llm()
    prompt = f"""You are a Neo4j Cypher expert. Convert the question below into a valid Cypher query.

Graph schema:
{schema}

Rules:
- Return ONLY the Cypher query, no explanation, no markdown, no backticks.
- Use only labels and relationship types that exist in the schema above.
- Always include a RETURN clause.
- Limit results to 25 with LIMIT 25 unless the question asks for a count.
- If the question cannot be answered from the schema, return:
  RETURN "Cannot answer from available graph schema" AS message

Question: {question}

Cypher:"""
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()


def run_cypher_query(cypher: str) -> list[dict]:
    """
    Execute a Cypher query and return results as a list of dicts.

    Teaching note: Neo4j returns Record objects. We convert each to
    a plain dict for display. Node and Relationship objects inside
    records are also converted to dicts so they render cleanly.
    """
    driver = get_neo4j_driver()
    if driver is None:
        return []
    try:
        with driver.session() as session:
            result = session.run(cypher)
            rows = []
            for record in result:
                row = {}
                for key in record.keys():
                    val = record[key]
                    if hasattr(val, "_properties"):
                        row[key] = dict(val._properties)
                    else:
                        row[key] = val
                rows.append(row)
            return rows
    except Exception as e:
        raise e


def run_cypher_write(cypher: str, params: dict = None) -> str:
    """
    Execute a write Cypher query (CREATE, MERGE, SET, DELETE).

    Returns a summary string describing what was created/modified.

    Teaching note: write queries use a separate code path from read
    queries. In Neo4j, session.run() works for both, but separating
    them in your code makes the intent explicit and makes it easier
    to add role-based access control later.
    """
    driver = get_neo4j_driver()
    if driver is None:
        return "Not connected to Neo4j."
    try:
        with driver.session() as session:
            result = session.run(cypher, params or {})
            summary = result.consume()
            counters = summary.counters
            parts = []
            if counters.nodes_created:
                parts.append(f"{counters.nodes_created} node(s) created")
            if counters.relationships_created:
                parts.append(f"{counters.relationships_created} relationship(s) created")
            if counters.properties_set:
                parts.append(f"{counters.properties_set} property/properties set")
            if counters.nodes_deleted:
                parts.append(f"{counters.nodes_deleted} node(s) deleted")
            return ", ".join(parts) if parts else "Query executed — no changes recorded."
    except Exception as e:
        raise e


# ── 9. LANGGRAPH AGENT (ChromaDB) ─────────────────────────────────────────────

# Agent state — passed between nodes in the graph
# Teaching note: TypedDict defines the shape of the state object.
# Every node reads from and writes to this shared state dict.
# add_messages is a LangGraph reducer — it appends new messages
# to the list rather than replacing it.
class AgentState(TypedDict):
    messages:         Annotated[list[BaseMessage], add_messages]
    retrieved_chunks: list[dict]
    no_context_found: bool


# System prompt — defines agent identity and hallucination guard
SYSTEM_PROMPT = """You are a helpful assistant answering questions from documents.

Rules you must follow without exception:
1. Answer ONLY from the provided context. Do not use general knowledge.
2. If the context does not contain enough information to answer, say:
   "I could not find relevant information in the uploaded documents."
   Do not guess or fill gaps from memory.
3. Always cite your source at the end of your answer using this format:
   Source: [filename]
4. Be concise and technically accurate."""


def retrieve_node(state: AgentState) -> dict:
    """
    Node 1 — Retrieve relevant chunks from ChromaDB.

    Reads the latest user message, queries the vector store,
    and sets no_context_found if nothing relevant is found.

    Teaching note: this node does NOT call the LLM. It only
    retrieves. Separation of retrieval and generation is what
    makes the pipeline testable and replaceable.
    """
    # Get the latest user message
    last_message = state["messages"][-1]
    query = last_message.content if hasattr(last_message, "content") else str(last_message)

    chunks = query_vector_store(query)

    if not chunks:
        return {
            "retrieved_chunks": [],
            "no_context_found": True,
        }

    return {
        "retrieved_chunks": chunks,
        "no_context_found": False,
    }


def generate_node(state: AgentState) -> dict:
    """
    Node 2 — Generate a response using retrieved chunks as context.

    Implements the hallucination guard: if no_context_found is True,
    returns a safe "not found" message without calling the LLM.

    Teaching note: the hallucination guard is the most important
    production RAG pattern. Without it, the LLM falls back to
    parametric memory and confidently answers from general knowledge
    rather than the uploaded documents.
    """
    llm = get_llm()

    # ── Hallucination guard ──────────────────────────────────────────
    if state["no_context_found"]:
        no_context = AIMessage(
            content="I could not find relevant information in the uploaded documents. "
                    "Please try rephrasing your question or upload relevant documents first."
        )
        return {"messages": [no_context]}

    # ── Build context string from retrieved chunks ───────────────────
    context_parts = []
    for chunk in state["retrieved_chunks"]:
        context_parts.append(
            f"[Source: {chunk['source']} | Score: {chunk['score']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # ── Build message list for the LLM ───────────────────────────────
    # Teaching note: we inject context as a system-level message
    # AFTER the main system prompt. The LLM sees:
    #   1. Who it is and what rules to follow (SYSTEM_PROMPT)
    #   2. The relevant document excerpts (context message)
    #   3. The full conversation history (state["messages"])
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        SystemMessage(content=f"Relevant document excerpts:\n\n{context}"),
        *state["messages"],
    ]

    response = llm.invoke(messages)
    return {"messages": [response]}


def build_agent():
    """
    Assemble and compile the LangGraph state graph.

    Graph structure:
        [START] → retrieve_node → generate_node → [END]

    Teaching note: compile() with no checkpointer means no persistent
    memory across sessions. For multi-turn conversation within a single
    session, we pass the full message history in state["messages"].
    """
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


@st.cache_resource
def get_agent():
    """Cache the compiled agent so it is built only once per session."""
    return build_agent()


def chat(query: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    Send a query to the agent and return the response.

    Converts the Streamlit chat history format (list of dicts with
    role/content keys) to LangChain message objects before invoking
    the graph.

    Returns:
        response_text: the agent's answer as a string
        sources: list of source chunk dicts used to generate the answer
    """
    agent = get_agent()

    # Convert history to LangChain message objects
    lc_messages = []
    for msg in history:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))

    # Add current query
    lc_messages.append(HumanMessage(content=query))

    result = agent.invoke({
        "messages":         lc_messages,
        "retrieved_chunks": [],
        "no_context_found": False,
    })

    # Extract response text
    response_text = result["messages"][-1].content

    # Extract sources used
    sources = result.get("retrieved_chunks", [])

    return response_text, sources


# ── 10. ASK ANYTHING ROUTER ───────────────────────────────────────────────────

def route_query(question: str) -> dict:
    """
    Use Groq to decide which databases are relevant to answer a question,
    then query each relevant database and return a combined result.

    Returns a dict with keys:
        "databases_used": list of DB names queried
        "reasoning":      Groq's explanation of routing decisions
        "results":        dict mapping DB name to its result string
        "synthesis":      Groq's final synthesised answer

    Teaching note: this is the highest-level RAG pattern in the app.
    Groq is used TWICE — once as a router (deciding which DBs to query)
    and once as a synthesiser (combining results into a coherent answer).
    The reasoning trace makes both decisions visible to students.
    """
    llm = get_llm()

    # Step 1 — Ask Groq which databases are relevant
    connection_status = check_all_connections()
    connected_dbs = [db for db, s in connection_status.items() if s["ok"]]

    routing_prompt = f"""You are a data routing expert. Given a question and a list of available databases,
decide which databases should be queried to best answer the question.

Available databases (only connected ones):
{chr(10).join(f"- {db}" for db in connected_dbs)}

Database roles:
- postgres: structured relational data, records, transactions, reporting
- mongo: flexible document data, variable schemas, logs, nested content
- chroma: semantic document search, policies, manuals, unstructured knowledge
- neo4j: graph relationships, networks, connections between entities

Question: {question}

Return a JSON object with exactly these keys:
{{
  "databases": ["list", "of", "db", "names", "to", "query"],
  "reasoning": "one sentence explaining why these databases were chosen"
}}

Return ONLY the JSON. No explanation, no markdown."""

    routing_response = llm.invoke([HumanMessage(content=routing_prompt)])

    try:
        import json
        routing = json.loads(routing_response.content.strip())
        dbs_to_query = [db for db in routing.get("databases", []) if db in connected_dbs]
        reasoning = routing.get("reasoning", "")
    except Exception:
        dbs_to_query = connected_dbs
        reasoning = "Routing parse failed — querying all connected databases."

    # Step 2 — Query each selected database
    results = {}

    if "postgres" in dbs_to_query:
        try:
            schema = get_postgres_schema()
            sql = nl_to_sql(question, schema)
            rows, cols = run_postgres_query(sql)
            if rows:
                df = pd.DataFrame(rows, columns=cols)
                results["postgres"] = f"SQL: {sql}\n\nResults:\n{df.to_string(index=False)}"
            else:
                results["postgres"] = f"SQL: {sql}\n\nNo results returned."
        except Exception as e:
            results["postgres"] = f"Query error: {e}"

    if "mongo" in dbs_to_query:
        try:
            collections = get_mongo_collections()
            if collections:
                col_name = collections[0]
                sample = get_collection_sample(col_name)
                query_str = nl_to_mongo_query(question, col_name, sample)
                mongo_results = run_mongo_query(col_name, query_str)
                results["mongo"] = f"Collection: {col_name}\nQuery: {query_str}\n\nResults: {str(mongo_results[:5])}"
            else:
                results["mongo"] = "No collections found."
        except Exception as e:
            results["mongo"] = f"Query error: {e}"

    if "chroma" in dbs_to_query:
        try:
            chunks = query_vector_store(question)
            if chunks:
                results["chroma"] = "\n\n".join(
                    [f"[{c['source']} | score: {c['score']}]\n{c['text']}" for c in chunks]
                )
            else:
                results["chroma"] = "No relevant documents found in vector store."
        except Exception as e:
            results["chroma"] = f"Query error: {e}"

    if "neo4j" in dbs_to_query:
        try:
            schema = get_neo4j_schema()
            cypher = nl_to_cypher(question, schema)
            neo4j_results = run_cypher_query(cypher)
            results["neo4j"] = f"Cypher: {cypher}\n\nResults: {str(neo4j_results[:10])}"
        except Exception as e:
            results["neo4j"] = f"Query error: {e}"

    # Step 3 — Synthesise results into a final answer
    if results:
        synthesis_prompt = f"""You are a data analyst. Synthesise the following database results
into a single, coherent answer to the user's question.

Question: {question}

Database results:
{chr(10).join([f"=== {db.upper()} ===\n{result}" for db, result in results.items()])}

Rules:
- Provide a direct, factual answer drawing from all available results.
- Mention which databases contributed to your answer.
- If results conflict, note the discrepancy.
- Be concise and professional."""

        synthesis_response = llm.invoke([HumanMessage(content=synthesis_prompt)])
        synthesis = synthesis_response.content
    else:
        synthesis = "No connected databases could be queried for this question."

    return {
        "databases_used": dbs_to_query,
        "reasoning":      reasoning,
        "results":        results,
        "synthesis":      synthesis,
    }


# ── 11. STREAMLIT UI ──────────────────────────────────────────────────────────

def init_session_state():
    """
    Initialise all session state keys on first run.

    Teaching note: Streamlit reruns the entire script on every user
    interaction. session_state persists values across reruns. We
    initialise all keys here defensively so no tab ever hits a
    KeyError mid-render.
    """
    defaults = {
        "chat_history":        [],
        "last_sources":        [],
        "pg_last_sql":         "",
        "pg_last_results":     None,
        "mongo_last_query":    "",
        "mongo_last_results":  None,
        "neo4j_last_cypher":   "",
        "neo4j_last_results":  None,
        "router_last_result":  None,
        "connection_status":   None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def render_sidebar():
    """
    Render the sidebar with connection health panel and app info.

    Teaching note: the health panel gives immediate visual feedback
    on which backends are reachable. In a classroom setting this is
    the first thing to check when something is not working.
    """
    st.sidebar.title("🗄️ RAG Capstone")
    st.sidebar.caption("PostgreSQL · MongoDB · ChromaDB · Neo4j · Groq")
    st.sidebar.divider()

    # Connection health panel
    st.sidebar.subheader("🔌 Connection Status")

    if st.sidebar.button("🔄 Retry Connections", use_container_width=True):
        # Clear cached connections so they are reattempted
        get_postgres_conn.clear()
        get_mongo_db.clear()
        get_chroma_collection.clear()
        get_neo4j_driver.clear()
        st.session_state.connection_status = None
        st.rerun()

    # Run health check (cached in session_state to avoid re-running on every rerender)
    if st.session_state.connection_status is None:
        st.session_state.connection_status = check_all_connections()

    status = st.session_state.connection_status

    labels = {
        "postgres": "PostgreSQL",
        "mongo":    "MongoDB",
        "chroma":   "ChromaDB",
        "neo4j":    "Neo4j",
    }

    for key, label in labels.items():
        s = status[key]
        icon = "🟢" if s["ok"] else "🔴"
        st.sidebar.markdown(f"{icon} **{label}**")
        if not s["ok"]:
            st.sidebar.caption(f"  ↳ {s['message']}")

    st.sidebar.divider()
    st.sidebar.caption(f"LLM: `{LLM_PROVIDER}` / `{GROQ_MODEL if LLM_PROVIDER == 'groq' else OLLAMA_MODEL}`")
    st.sidebar.caption(f"Embeddings: `{EMBEDDING_MODEL}`")


def render_postgres_tab():
    """Render the PostgreSQL natural-language query interface."""
    st.header("🐘 PostgreSQL")

    conn = get_postgres_conn()
    if conn is None:
        st.error("PostgreSQL is not connected. Check your .env credentials and click Retry Connections in the sidebar.")
        return

    # Schema viewer (collapsible)
    with st.expander("📋 Database Schema", expanded=False):
        schema = get_postgres_schema()
        st.code(schema, language="text")

    # Natural language query
    st.subheader("Ask a Question")
    question = st.text_input("Enter your question in plain English", key="pg_question")

    if st.button("Run Query", key="pg_run"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Generating SQL and querying database..."):
                try:
                    schema = get_postgres_schema()
                    sql = nl_to_sql(question, schema)
                    rows, cols = run_postgres_query(sql)
                    st.session_state.pg_last_sql     = sql
                    st.session_state.pg_last_results = (rows, cols)
                except Exception as e:
                    st.error(f"Query failed: {e}")
                    st.session_state.pg_last_sql = ""

    # Display results
    if st.session_state.pg_last_sql:
        st.subheader("Generated SQL")
        st.code(st.session_state.pg_last_sql, language="sql")

    if st.session_state.pg_last_results:
        rows, cols = st.session_state.pg_last_results
        st.subheader("Results")
        if rows:
            df = pd.DataFrame(rows, columns=cols)
            st.dataframe(df, use_container_width=True)
            st.caption(f"{len(df)} row(s) returned")
        else:
            st.info("Query returned no results.")


def render_mongo_tab():
    """Render the MongoDB natural-language query interface."""
    st.header("🍃 MongoDB")

    db = get_mongo_db()
    if db is None:
        st.error("MongoDB is not connected. Check your MONGO_URI in .env and click Retry Connections in the sidebar.")
        return

    collections = get_mongo_collections()
    if not collections:
        st.warning("No collections found. Create a collection and add documents to your MongoDB database.")
        return

    # Collection browser
    selected_collection = st.selectbox("Select Collection", collections, key="mongo_collection")

    with st.expander("📄 Sample Documents", expanded=False):
        sample = get_collection_sample(selected_collection, limit=3)
        for doc in sample:
            st.json(doc)

    # Natural language query
    st.subheader("Ask a Question")
    question = st.text_input("Enter your question in plain English", key="mongo_question")

    if st.button("Run Query", key="mongo_run"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Generating MongoDB query..."):
                try:
                    sample_docs = get_collection_sample(selected_collection)
                    query_str = nl_to_mongo_query(question, selected_collection, sample_docs)
                    results = run_mongo_query(selected_collection, query_str)
                    st.session_state.mongo_last_query   = query_str
                    st.session_state.mongo_last_results = results
                except Exception as e:
                    st.error(f"Query failed: {e}")

    # Display results
    if st.session_state.mongo_last_query:
        st.subheader("Generated Query")
        st.code(st.session_state.mongo_last_query, language="python")

    if st.session_state.mongo_last_results is not None:
        st.subheader("Results")
        results = st.session_state.mongo_last_results
        if results:
            st.write(f"{len(results)} document(s) returned")
            for doc in results[:20]:
                st.json(doc)
        else:
            st.info("Query returned no documents.")


def render_chroma_tab():
    """Render the ChromaDB document ingestion and RAG chat interface."""
    st.header("🔍 ChromaDB")

    collection = get_chroma_collection()
    if collection is None:
        st.error("ChromaDB could not be initialised. Check CHROMA_PERSIST_PATH in .env.")
        return

    mode = st.radio("Mode", ["Ingest Documents", "Query Knowledge Base"], horizontal=True, key="chroma_mode")

    if mode == "Ingest Documents":
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF, Markdown, or text files",
            type=["pdf", "md", "txt"],
            accept_multiple_files=True,
            key="chroma_uploader",
        )

        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.slider("Chunk size (characters)", 256, 1024, CHUNK_SIZE, key="chunk_size")
        with col2:
            st.metric("Documents in store", collection.count())

        if uploaded_files and st.button("⬆ Ingest Documents", key="chroma_ingest"):
            with st.spinner("Ingesting..."):
                result = ingest_documents(uploaded_files)
            if result["errors"]:
                for err in result["errors"]:
                    st.error(f"Error: {err}")
            else:
                st.success(f"✅ {result['ingested']} chunks added ({result['skipped']} duplicates skipped)")

        # Corpus stats
        stats = get_collection_stats()
        if stats["total_chunks"] > 0:
            st.subheader("Corpus")
            st.metric("Total chunks", stats["total_chunks"])
            st.write("**Sources:**")
            for source in stats["sources"]:
                st.caption(f"• {source}")

    else:  # Query mode
        # Reuse the existing chat interface from Lab 3
        st.subheader("Chat with Your Knowledge Base")

        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if st.session_state.last_sources:
            with st.expander("📎 Sources used in last response", expanded=False):
                for chunk in st.session_state.last_sources:
                    st.caption(f"**{chunk['source']}** — score: `{chunk['score']}`")
                    st.markdown(f"> {chunk['text'][:300]}...")
                    st.divider()

        if query := st.chat_input("Ask a question about your documents...", key="chroma_chat"):
            with st.chat_message("user"):
                st.markdown(query)
            st.session_state.chat_history.append({"role": "user", "content": query})

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response, sources = chat(query, st.session_state.chat_history[:-1])
                st.markdown(response)

            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.session_state.last_sources = sources
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑 Clear chat", key="chroma_clear"):
                st.session_state.chat_history = []
                st.session_state.last_sources = []
                st.rerun()


def render_neo4j_tab():
    """Render the Neo4j graph load and exploration interface."""
    st.header("🕸️ Neo4j")

    driver = get_neo4j_driver()
    if driver is None:
        st.error("Neo4j is not connected. Check NEO4J_URI and NEO4J_PASSWORD in .env and click Retry Connections in the sidebar.")
        return

    mode = st.radio("Mode", ["Load Data", "Explore Graph"], horizontal=True, key="neo4j_mode")

    if mode == "Load Data":
        st.subheader("Create Nodes and Relationships")
        st.info("Write Cypher CREATE or MERGE statements to populate your graph. Tip: use MERGE to avoid duplicates.")

        cypher_input = st.text_area(
            "Cypher (CREATE or MERGE statements)",
            height=200,
            placeholder="MERGE (n:Person {name: 'Alice'})\nMERGE (m:Person {name: 'Bob'})\nMERGE (n)-[:KNOWS]->(m)",
            key="neo4j_write_cypher",
        )

        if st.button("▶ Execute", key="neo4j_write_run"):
            if not cypher_input.strip():
                st.warning("Please enter a Cypher statement.")
            else:
                with st.spinner("Executing..."):
                    try:
                        summary = run_cypher_write(cypher_input)
                        st.success(f"✅ {summary}")
                    except Exception as e:
                        st.error(f"Execution failed: {e}")

        # Schema viewer
        with st.expander("📋 Graph Schema", expanded=False):
            schema = get_neo4j_schema()
            st.code(schema, language="text")

    else:  # Explore mode
        st.subheader("Ask a Question About Your Graph")

        with st.expander("📋 Graph Schema", expanded=False):
            schema = get_neo4j_schema()
            st.code(schema, language="text")

        question = st.text_input("Ask a question about relationships in your data", key="neo4j_question")

        if st.button("Run Query", key="neo4j_run"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Generating Cypher and querying graph..."):
                    try:
                        schema = get_neo4j_schema()
                        cypher = nl_to_cypher(question, schema)
                        results = run_cypher_query(cypher)
                        st.session_state.neo4j_last_cypher  = cypher
                        st.session_state.neo4j_last_results = results
                    except Exception as e:
                        st.error(f"Query failed: {e}")

        if st.session_state.neo4j_last_cypher:
            st.subheader("Generated Cypher")
            st.code(st.session_state.neo4j_last_cypher, language="cypher")

        if st.session_state.neo4j_last_results is not None:
            st.subheader("Results")
            results = st.session_state.neo4j_last_results
            if results:
                st.write(f"{len(results)} record(s) returned")
                # Render path-style display for relationship results
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Query returned no results.")


def render_ask_anything_tab():
    """Render the multi-database routing and synthesis interface."""
    st.header("✨ Ask Anything")
    st.caption("Groq reads your question, decides which databases to query, and synthesises a unified answer.")

    question = st.text_input("Ask any question about your business data", key="router_question")

    if st.button("🔍 Ask", key="router_run", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Routing query across databases..."):
                result = route_query(question)
                st.session_state.router_last_result = result

    if st.session_state.router_last_result:
        r = st.session_state.router_last_result

        # Synthesised answer — shown first and prominently
        st.subheader("Answer")
        st.markdown(r["synthesis"])

        st.divider()

        # Reasoning trace — the key teaching artefact
        st.subheader("🧠 Reasoning Trace")
        st.info(f"**Databases queried:** {', '.join(r['databases_used']) if r['databases_used'] else 'None'}")
        st.caption(f"**Routing reasoning:** {r['reasoning']}")

        # Raw results per database (collapsible)
        if r["results"]:
            with st.expander("📊 Raw Results by Database", expanded=False):
                for db_name, db_result in r["results"].items():
                    st.markdown(f"**{db_name.upper()}**")
                    st.code(db_result, language="text")
                    st.divider()


def main():
    """Application entry point."""
    st.set_page_config(
        page_title="RAG Capstone",
        page_icon="🗄️",
        layout="wide",
    )

    init_session_state()
    render_sidebar()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🐘 PostgreSQL",
        "🍃 MongoDB",
        "🔍 ChromaDB",
        "🕸️ Neo4j",
        "✨ Ask Anything",
    ])

    with tab1:
        render_postgres_tab()
    with tab2:
        render_mongo_tab()
    with tab3:
        render_chroma_tab()
    with tab4:
        render_neo4j_tab()
    with tab5:
        render_ask_anything_tab()


if __name__ == "__main__":
    main()
