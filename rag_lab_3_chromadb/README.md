# RAG Demo
### LangChain · LangGraph · ChromaDB · Streamlit · Groq

A single-file RAG (Retrieval-Augmented Generation) application. Upload documents and chat with your knowledge
base using a local vector store and a free LLM.

**LangChain** is a Python framework for building applications powered by large language models. It provides a standardized set of building blocks so you are not writing low-level API calls from scratch every time.

The three things it does that matter most for this app:

**1. Abstracts LLM providers**
`ChatGroq`, `ChatOllama`, and `ChatOpenAI` all work the same way in your code. You call `.invoke(messages)` and get back a response regardless of which provider is underneath. Switching providers is a one-line change.

**2. Handles document loading and splitting**
LangChain provides loaders for dozens of file types — PDF, Markdown, Word, HTML, databases, and more — plus text splitters that chunk documents intelligently. Without this you would be writing your own PDF parser and chunking logic.

**3. Provides the message format LangGraph expects**
`HumanMessage`, `AIMessage`, and `SystemMessage` are LangChain objects that represent turns in a conversation. LangGraph is built on top of LangChain and uses these same objects for its state — which is why they work together cleanly.

A useful mental model: if LangGraph is the plumbing that controls *how* your agent flows, LangChain is the toolbox that provides the *parts* — the LLM connections, the document loaders, the message types. Most real LLM applications use both.

---

## What This App Does

This app demonstrates the full RAG pipeline in one readable file:

1. You upload one or more documents (PDF, Markdown, or text)
2. The app splits them into chunks and converts each chunk into a
   numerical vector (embedding) using a local model
3. Those vectors are stored in ChromaDB — a local vector database
4. When you ask a question, your question is also converted to a vector
5. ChromaDB finds the document chunks most similar to your question
6. Those chunks are passed to the LLM (Groq or Ollama) as context
7. The LLM generates an answer grounded in your documents

The agent is built with LangGraph — a framework for building stateful,
multi-step AI workflows. It manages the flow from retrieval to generation
and enforces rules like the hallucination guard.

```
Your question
     │
     ▼
[Embed question] ──→ ChromaDB similarity search
                              │
                       Retrieved chunks
                              │
                              ▼
               [LangGraph: retrieve → generate]
                              │
                       Answer + citations
```

---

## Tech Stack

| Component | Library | Purpose |
|---|---|---|
| Document loading | LangChain Community | Load PDF, MD, TXT files |
| Text splitting | LangChain Text Splitters | Chunk documents |
| Embeddings | sentence-transformers | Convert text to vectors locally |
| Vector store | ChromaDB | Store and search vectors |
| Agent orchestration | LangGraph | Manage retrieve → generate flow |
| LLM (cloud) | Groq + LangChain | Fast free LLM inference |
| LLM (local) | Ollama + LangChain | Local fallback, no API key |
| UI | Streamlit | Interactive web interface |
| Config | python-dotenv | Load .env credentials |

---

## Before You Start — Prerequisites

### 1. Get a GROQ API - there is a generous free tier available.

### 2. UV Package Manager
UV is a fast modern Python package manager that replaces pip.

**Mac / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:
```bash
uv --version
```

### 3. Choose Your LLM Provider

You need at least one of the following before running the app.

---

#### Option A — Groq (Recommended: free, fast, cloud-based)

Groq provides free API access to open source models (Llama, Mixtral)
using their custom LPU hardware. No GPU required on your machine.

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Click **API Keys** in the left sidebar
4. Click **Create API Key**
5. Copy the key — you will add it to `.env` in the setup steps below

Free tier models available:
- `llama-3.1-8b-instant` — fast, good for demos (default)
- `llama-3.1-70b-versatile` — higher quality, slightly slower
- `mixtral-8x7b-32768` — good for longer documents

---

#### Option B — Ollama (Local, no API key, runs offline)

Ollama runs open source LLMs entirely on your machine.
No internet connection required after setup. No API costs ever.

1. Download from [ollama.com](https://ollama.com) and install
2. Open a terminal and pull a model:
```bash
ollama pull llama3.2        # small and fast (recommended for class)
ollama pull mistral         # better quality, needs more RAM
```
3. Start the Ollama server (must be running before the app):
```bash
ollama serve
```
4. Verify it is running:
```bash
curl http://localhost:11434/api/tags
```
You should see a JSON response listing your downloaded models.

To use Ollama instead of Groq, set `LLM_PROVIDER=ollama` in your `.env`
file. This is a great live demo moment — the same app, same code,
different backend.

---

## Setup

### Step 1 — Get the project files
```bash
cd your-projects-folder
git clone <repo-url>
cd rag_lab_3_vector_store
```

### Step 2 — Install dependencies
```bash
uv sync
```
This reads `pyproject.toml` and installs everything into a local
`.venv` folder. No separate `pip install` needed.

### Step 3 — Configure your environment
```bash
cp .env.example .env
```
Open `.env` in any text editor and fill in your credentials:

```
# For Groq:
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant

# For Ollama (swap these in instead):
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=llama3.2
```

### Step 4 — Pre-load the embedding model (do this before class)

The app uses `all-MiniLM-L6-v2`, a ~90MB embedding model that runs
locally on your CPU. It downloads automatically on first use but this
can take several minutes and will make the app appear frozen if you
have not done this step in advance.

Run this once before your first demo to cache the model permanently:

```bash
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); print('Model ready')"
```

Wait for `Model ready` to print. After this the model is cached locally
and loads in seconds on every subsequent run.

### Step 5 — Run the app
```bash
uv run streamlit run app.py
```
Or with the venv already activated:
```bash
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

---

## How to Use the App

**Upload documents**
Use the sidebar on the left. Click Browse files or drag and drop.
PDF, Markdown (.md), and plain text (.txt) are supported.
Click **Ingest Documents** to process and store them in ChromaDB.

**Chat**
Type a question in the chat input at the bottom of the main area.
The app retrieves relevant document chunks and generates a grounded answer.

**View sources**
After each response, click **Sources used in last response** to see
which document chunks were retrieved and their similarity scores.

**Clear chat**
Click **Clear chat** to start a new conversation. Note: ChromaDB is not
cleared — your ingested documents remain available until you delete the
`chroma_db/` folder manually.

**Try the hallucination guard**
Ask a question completely unrelated to your documents (e.g. "What is
the capital of France" when you have uploaded a database paper). The
app should respond with "I could not find relevant information" rather
than answering from general knowledge.

---

## Code Walkthrough — Section by Section

The entire app lives in `app.py`, organized into six labeled sections.

---

### Section 1 — Imports

```python
import hashlib, os, tempfile
from langchain_community.document_loaders import PyPDFLoader ...
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph ...
import chromadb
import streamlit as st
```

All dependencies are imported at the top of the file. A few worth
noting:

`hashlib` is used to generate deterministic chunk IDs for duplicate
detection. `tempfile` is needed because Streamlit gives us file objects
but LangChain loaders need file paths on disk — we write to a temp file,
load it, then delete it immediately. `load_dotenv()` reads the `.env`
file and puts all values into environment variables so `os.getenv()`
can access them anywhere in the file.

---

### Section 2 — Configuration

```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
RETRIEVAL_K = 4
SIMILARITY_THRESHOLD = 0.3
SYSTEM_PROMPT = """..."""
```

All tunable parameters live here as module-level constants. No magic
numbers are buried inside functions. If you want to experiment with
retrieval quality, this is the only place you need to change.

**LLM_PROVIDER** — reads from `.env`. Set to `"groq"` or `"ollama"`.
The `get_llm()` function in Section 5 reads this and returns the
appropriate LangChain chat model. Switching providers requires only
changing this one value — no other code changes.

**CHUNK_SIZE (512)** — maximum characters per chunk. Too large and
retrieval returns chunks that are too broad; too small and individual
chunks lack enough context to answer questions. 512 is a reasonable
starting point for most documents.

**CHUNK_OVERLAP (50)** — characters shared between adjacent chunks.
Without overlap, a concept that spans a chunk boundary gets cut in half
and neither chunk contains the complete idea. Overlap prevents this.

**RETRIEVAL_K (4)** — number of chunks retrieved per query. More chunks
give the LLM more context but increase token usage and response time.

**SIMILARITY_THRESHOLD (0.3)** — the hallucination guard threshold.
Similarity scores range from 0.0 (completely unrelated) to 1.0
(identical). Chunks scoring below 0.3 are discarded. If no chunks meet
the threshold, the system returns a "not found" message instead of
letting the LLM answer from general knowledge. Raise this for stricter
matching, lower it to cast a wider net.

**SYSTEM_PROMPT** — instructions given to the LLM before every
conversation. Tells it to answer only from retrieved context, cite
sources, and say so honestly when it cannot find an answer.

---

### Section 3 — Document Processing

Three functions that transform a raw uploaded file into chunks
ready for embedding.

**`generate_doc_id(filename, content)`**
Creates a 16-character ID by hashing the filename and the first 500
characters of content using SHA-256. Because the same content always
produces the same hash, uploading the same file twice always produces
the same IDs. This is content-addressed storage — the foundation of
duplicate detection. A timestamp-based ID would create a new entry on
every upload regardless of whether the content changed.

**`load_file(uploaded_file)`**
Detects the file type by extension and routes to the appropriate
LangChain loader. `PyPDFLoader` handles PDFs page by page,
`UnstructuredMarkdownLoader` parses Markdown structure, and
`TextLoader` handles plain text. Each loader returns a list of
LangChain `Document` objects containing the text and metadata. The
original filename is attached to every document's metadata so citations
are accurate in responses.

**`chunk_documents(docs)`**
Splits documents using `RecursiveCharacterTextSplitter`. The splitter
tries natural boundaries first — double newline, then single newline,
then sentence end, then word boundary — before falling back to hard
character splits. This produces semantically coherent chunks compared
to splitting at fixed positions.

---

### Section 4 — Vector Store

Five functions that manage ChromaDB.

**`get_embedding_model()`** decorated with `@st.cache_resource`
Loads the `all-MiniLM-L6-v2` model from sentence-transformers.
`@st.cache_resource` means this runs exactly once per application
session. Without it, Streamlit would reload the 90MB model on every
button click because it reruns the entire script on every interaction.

The embedding model converts text into a list of 384 numbers that
capture the semantic meaning of the text. Similar sentences produce
similar vectors, which is what makes similarity search possible.
This model runs entirely on your CPU — no GPU or API key required.

**`get_chroma_collection()`** decorated with `@st.cache_resource`
Initializes a `PersistentClient` pointing to `./chroma_db`. Persistent
means the data is written to disk and survives restarts — documents
ingested today are still there tomorrow. The collection uses cosine
similarity (`hnsw:space: cosine`) which measures the angle between
vectors rather than their Euclidean distance, making it scale-invariant
and well-suited for text comparison.

**`check_duplicate(collection, doc_id)`**
Calls `collection.get(ids=[doc_id])` and returns True if the ID already
exists. Duplicate chunks are skipped during ingestion, preventing the
vector store from growing unboundedly when the same documents are
re-uploaded.

**`ingest_documents(uploaded_files)`**
The complete ingestion pipeline: load → chunk → generate ID → check
duplicate → embed → upsert into ChromaDB. Returns a result dict with
counts of ingested and skipped chunks and any errors encountered. This
is the function called when the user clicks Ingest Documents.

**`query_vector_store(query)`**
Embeds the query text, calls `collection.query()` to find the top-k
most similar chunks, and converts cosine distances to similarity scores
using `score = 1 - distance`. Chunks below `SIMILARITY_THRESHOLD` are
filtered out. Returns an empty list if nothing relevant is found —
this empty list is what triggers the hallucination guard in the agent.

---

### Section 5 — LangGraph Agent

The agent is a directed state graph with two nodes. LangGraph manages
the state and the execution flow between them.

**A directed state graph** is a flowchart where:

- **Nodes** are steps that do work — functions that receive input, process it, and produce output
- **Edges** are arrows that connect nodes — they define what runs next
- **Directed** means the arrows only go one way — there is no going backward unless you explicitly draw a backward arrow
- **State** is a shared data object that every node can read from and write to — it travels through the graph and accumulates results as it goes

Think of it like an assembly line. Each station (node) receives the current state of the product, does its job, updates the product, and passes it to the next station. The product at any point reflects everything that has been done to it so far.

---

**In this app specifically:**

```
[START] → retrieve_node → generate_node → [END]
```

The **state** object looks like this at the start of each request:
```python
{
    "messages": [HumanMessage("What is normalization?")],
    "retrieved_chunks": [],
    "no_context_found": False
}
```

`retrieve_node` receives that state, queries ChromaDB, and returns updates:
```python
{
    "retrieved_chunks": [chunk1, chunk2, chunk3],
    "no_context_found": False
}
```

LangGraph merges those updates into the state and passes it forward.

`generate_node` receives the updated state — now it has both the original question and the retrieved chunks — builds a prompt, calls the LLM, and returns:
```python
{
    "messages": [AIMessage("Normalization is...")]
}
```

LangGraph merges that in too and the graph reaches `[END]`.

---

**Why this matters over just calling functions directly:**

You could write `generate(retrieve(query))` without LangGraph and get the same result for this simple case. LangGraph becomes valuable when you need conditional branching (go to node A or node B depending on what was found), loops (retry if the first retrieval failed), human-in-the-loop pauses, or persistent memory across sessions. The graph makes all of that explicit and auditable — you can see the entire decision structure without reading the implementation of every function.

**`AgentState` (TypedDict)**
Defines the shape of the shared state object passed between nodes.
Every node reads from and writes to this same state dict:
- `messages` — full conversation history as LangChain message objects.
  The `add_messages` reducer appends new messages rather than
  overwriting the list, which is what enables multi-turn conversation.
- `retrieved_chunks` — chunks returned by the retrieval node
- `no_context_found` — boolean flag set when the similarity threshold
  is not met by any retrieved chunk

**`get_llm()`** decorated with `@st.cache_resource`
Returns either `ChatGroq` or `ChatOllama` based on `LLM_PROVIDER`.
Both implement the same `BaseChatModel` interface from LangChain.
Switching providers requires only changing one environment variable —
no downstream code changes anywhere else. This is the strategy pattern:
the same interface with swappable implementations.

**`retrieve_node(state)`**
Node 1. Extracts the latest user message from state, queries the vector
store, and writes the results back to state. This node deliberately does
not call the LLM. Keeping retrieval and generation separate makes each
independently testable and replaceable without touching the other.

**`generate_node(state)`**
Node 2. Checks `no_context_found` first. If True, returns a safe "not
found" message without calling the LLM at all — this is the
hallucination guard. Without it, the LLM would fall back to its
training data and confidently answer from general knowledge instead of
the uploaded documents. If relevant chunks were found, builds a prompt
with the system instructions, the retrieved chunks as context, and the
conversation history, then calls the LLM and appends the response.

**`build_agent()`**
Assembles the graph:
```
[START] → retrieve_node → generate_node → [END]
```
`graph.compile()` validates the structure and returns a runnable object.
No checkpointer is used — conversation memory is maintained by passing
the full message history in state on every invocation.

---

### Section 6 — Streamlit UI

Four functions that build the interface.

**`init_session_state()`**
Initializes `st.session_state` keys on first run. Streamlit reruns the
entire Python script on every user interaction. Session state is the
mechanism for persisting values across reruns. Without it, the chat
history would reset to empty on every message sent.

**`render_sidebar()`**
Builds the left panel with the file uploader, ingest button, corpus
statistics (total chunks, source filenames), and LLM provider info.
The sidebar remains visible at all times so users can see what is
currently ingested without leaving the chat.

**`render_chat()`**
Renders the chat history, the sources expander from the last response,
and the chat input at the bottom. When the user submits a query the
function appends it to history, calls the agent, renders the response,
stores the source chunks, and calls `st.rerun()` to refresh the page.

**`main()`**
Entry point. Sets page config, initializes session state, renders the
header and clear button, then calls `render_sidebar()` and
`render_chat()`. The `if __name__ == "__main__":` guard at the bottom
ensures `main()` only runs when executed directly, not if the file
is imported as a module by another script.

---

## Switching Between Groq and Ollama Live

Open `.env` and change
one line, then restart the app:

```
# Cloud inference:
LLM_PROVIDER=groq

# Local inference:
LLM_PROVIDER=ollama
```

The retrieval pipeline, LangGraph graph, and UI are completely
unchanged. The `get_llm()` function returns a different object but
nothing else in the codebase knows or cares. This is what abstraction
buys you in a production system.

---

## Tuning Tips

| Goal | Change |
|---|---|
| More precise retrieval | Increase `SIMILARITY_THRESHOLD` (try 0.5) |
| Broader retrieval | Decrease `SIMILARITY_THRESHOLD` (try 0.2) |
| More context per answer | Increase `RETRIEVAL_K` (try 6) |
| Faster ingestion | Decrease `CHUNK_SIZE` (try 256) |
| Better context coherence | Increase `CHUNK_OVERLAP` (try 100) |
| Stricter answers | Add more constraints to `SYSTEM_PROMPT` |

---

## Resetting the Vector Store

The `chroma_db/` folder persists between sessions. To start fresh:

**Mac / Linux:**
```bash
rm -rf chroma_db/
```
**Windows:**
```powershell
Remove-Item -Recurse -Force chroma_db
```
Restart the app. The folder is recreated automatically on next ingest.

---

## Project Structure

```
5707-rag/
├── app.py              ← entire application — one file
├── pyproject.toml      ← UV dependencies
├── .env.example        ← environment variable template
├── .env                ← your credentials (never commit this)
├── chroma_db/          ← auto-created, persists vector data
└── README.md
```

---

## Common Issues

**App appears frozen on first load**
The embedding model is downloading. Run the pre-load command in
Step 4 of Setup before class to prevent this.

**`GROQ_API_KEY` error**
Your `.env` file is missing or the key is incorrect. Confirm `.env`
exists in the same folder as `app.py` and contains a valid key.

**`ollama: connection refused`**
Ollama is not running. Open a separate terminal and run `ollama serve`
before starting the app.

**Answers seem unrelated to documents**
Lower `SIMILARITY_THRESHOLD` — your chunks may not be scoring above
0.3. Check the Sources panel after a query to see actual scores.

**`chroma_db` errors after reinstall**
Delete the `chroma_db/` folder and re-ingest your documents. The
folder format can change between ChromaDB versions.
