"""
app.py
======
RAG Demo — LangChain + LangGraph + ChromaDB + Streamlit + Groq
Data Modeling Class — Single File Teaching App

Sections:
  1. IMPORTS
  2. CONFIGURATION
  3. DOCUMENT PROCESSING
  4. VECTOR STORE
  5. LANGGRAPH AGENT
  6. STREAMLIT UI

Run with:
    uv run streamlit run app.py
"""

# ── 1. IMPORTS ───────────────────────────────────────────────────────────────

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Annotated

import chromadb
import streamlit as st
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

load_dotenv()

# ── 2. CONFIGURATION ─────────────────────────────────────────────────────────

# LLM provider — switch to "ollama" to demo local fallback in class
# Teaching note: same LangChain interface, different backend, zero
# code changes downstream. This is the abstraction pattern.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

# Groq settings
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL     = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Ollama settings (fallback — requires ollama serve running locally)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

# Embedding model
# Teaching note: all-MiniLM-L6-v2 downloads ~90MB on first run only.
# Run the app once before class so the model is cached locally.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ChromaDB — persistent local storage
CHROMA_DB_PATH   = "./chroma_db"
COLLECTION_NAME  = "rag_demo"

# Retrieval settings
CHUNK_SIZE        = 512
CHUNK_OVERLAP     = 50
RETRIEVAL_K       = 4
SIMILARITY_THRESHOLD = 0.3   # chunks below this score are discarded

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

# ── 3. DOCUMENT PROCESSING ───────────────────────────────────────────────────

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
            loader = UnstructuredMarkdownLoader(tmp_path)
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


# ── 4. VECTOR STORE ──────────────────────────────────────────────────────────

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


@st.cache_resource
def get_chroma_collection():
    """
    Initialize and cache the persistent ChromaDB collection.

    Teaching note: PersistentClient saves data to disk at CHROMA_DB_PATH.
    The collection survives application restarts — documents ingested in
    one session are available in the next. Compare this to EphemeralClient
    which loses everything when the app stops.
    """
    Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},  # cosine similarity for text
    )
    return collection


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


# ── 5. LANGGRAPH AGENT ───────────────────────────────────────────────────────

# Agent state — passed between nodes in the graph
# Teaching note: TypedDict defines the shape of the state object.
# Every node reads from and writes to this shared state dict.
# add_messages is a LangGraph reducer — it appends new messages
# to the list rather than replacing it.
class AgentState(TypedDict):
    messages:       Annotated[list[BaseMessage], add_messages]
    retrieved_chunks: list[dict]
    no_context_found: bool


@st.cache_resource
def get_llm():
    """
    Load and cache the LLM based on LLM_PROVIDER config.

    Teaching note: both ChatGroq and ChatOllama implement the same
    LangChain BaseChatModel interface. Switching providers requires
    only changing LLM_PROVIDER — no downstream code changes.
    This is the abstraction pattern / strategy pattern in practice.
    """
    if LLM_PROVIDER == "ollama":
        return ChatOllama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
        )
    else:  # default: groq
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
        )


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
        "messages":        lc_messages,
        "retrieved_chunks": [],
        "no_context_found": False,
    })

    # Extract response text
    response_text = result["messages"][-1].content

    # Extract sources used
    sources = result.get("retrieved_chunks", [])

    return response_text, sources


# ── 6. STREAMLIT UI ──────────────────────────────────────────────────────────

def init_session_state():
    """
    Initialise all session state keys on first run.

    Teaching note: Streamlit reruns the entire script on every
    user interaction. session_state persists values across reruns.
    Without this, chat history would be lost on every message.
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []


def render_sidebar():
    """Render the document ingestion panel in the sidebar."""
    st.sidebar.title("📂 Documents")

    # File uploader
    uploaded_files = st.sidebar.file_uploader(
        "Upload documents",
        type=["pdf", "md", "txt"],
        accept_multiple_files=True,
        help="Upload PDF, Markdown, or text files to add to the knowledge base.",
    )

    # Ingest button
    if uploaded_files:
        if st.sidebar.button("⬆ Ingest Documents", use_container_width=True):
            with st.spinner("Ingesting documents..."):
                result = ingest_documents(uploaded_files)

            if result["errors"]:
                for err in result["errors"]:
                    st.sidebar.error(f"Error: {err}")
            else:
                st.sidebar.success(
                    f"✅ {result['ingested']} chunks added "
                    f"({result['skipped']} duplicates skipped)"
                )

    # Corpus stats
    st.sidebar.divider()
    st.sidebar.subheader("📊 Corpus")
    stats = get_collection_stats()

    if stats["total_chunks"] == 0:
        st.sidebar.info("No documents ingested yet.")
    else:
        st.sidebar.metric("Total chunks", stats["total_chunks"])
        st.sidebar.write("**Sources:**")
        for source in stats["sources"]:
            st.sidebar.caption(f"• {source}")

    # Provider info
    st.sidebar.divider()
    st.sidebar.caption(f"LLM: `{LLM_PROVIDER}` / `{GROQ_MODEL if LLM_PROVIDER == 'groq' else OLLAMA_MODEL}`")
    st.sidebar.caption(f"Embeddings: `{EMBEDDING_MODEL}`")
    st.sidebar.caption(f"Vector store: ChromaDB local")


def render_chat():
    """Render the main chat interface."""

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Show sources from last response
    if st.session_state.last_sources:
        with st.expander("📎 Sources used in last response", expanded=False):
            for chunk in st.session_state.last_sources:
                st.caption(
                    f"**{chunk['source']}** — similarity score: `{chunk['score']}`"
                )
                st.markdown(f"> {chunk['text'][:300]}...")
                st.divider()

    # Chat input
    if query := st.chat_input("Ask a question about your documents..."):

        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(query)

        # Add to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": query,
        })

        # Get response from agent
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = chat(
                    query,
                    st.session_state.chat_history[:-1],  # history before this query
                )
            st.markdown(response)

        # Store response and sources
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response,
        })
        st.session_state.last_sources = sources

        st.rerun()


def main():
    """Application entry point."""
    st.set_page_config(
        page_title="RAG Demo",
        page_icon="🔍",
        layout="wide",
    )

    init_session_state()

    # Header
    st.title("🔍 RAG Demo")
    st.caption(
        "LangChain · LangGraph · ChromaDB · Groq — "
        "Upload documents and chat with your knowledge base."
    )

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑 Clear chat", type="secondary"):
            st.session_state.chat_history = []
            st.session_state.last_sources = []
            st.rerun()

    st.divider()

    # Render panels
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
