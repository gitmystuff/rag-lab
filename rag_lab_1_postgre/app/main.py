from fastapi import FastAPI, HTTPException
from app.db import get_conn
from app.models import DocumentCreate

app = FastAPI(title="RAG Data API")


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/documents")
def create_document(doc: DocumentCreate):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (title, source)
                VALUES (%s, %s)
                RETURNING id, title, source, created_at
                """,
                (doc.title, doc.source),
            )
            return cur.fetchone()


@app.get("/documents")
def list_documents():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM documents ORDER BY created_at DESC")
            return cur.fetchall()


@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Document not found")
            return row


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
            return {"status": "deleted"}
