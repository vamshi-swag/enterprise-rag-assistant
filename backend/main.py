from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os
import logging
from backend.rag import add_document, query_documents, clear_all_documents, uploaded_files_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG API",
    description="Enterprise RAG Knowledge Assistant — multi-document Q&A powered by LangChain, ChromaDB and Groq",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


class Query(BaseModel):
    query: str


@app.get("/")
def home():
    return {"message": "RAG API is running", "status": "healthy"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "documents_loaded": len(uploaded_files_registry),
        "files": uploaded_files_registry,
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and add a PDF to the shared knowledge base."""

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Prevent uploading the same file twice
    if file.filename in uploaded_files_registry:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename} is already uploaded. Upload a different file."
        )

    file_path = os.path.join(TEMP_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved: {file_path}")

        chunks_added = add_document(file_path, file.filename)

        return {
            "message": f"{file.filename} added to knowledge base.",
            "filename": file.filename,
            "chunks_added": chunks_added,
            "total_documents": len(uploaded_files_registry),
            "all_documents": uploaded_files_registry,
        }

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process file.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Temp file removed: {file_path}")


@app.post("/chat")
async def chat(q: Query):
    """Ask a question across all uploaded documents."""

    if not q.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    if not uploaded_files_registry:
        raise HTTPException(
            status_code=400,
            detail="No documents loaded. Please upload at least one PDF first.",
        )

    try:
        result = query_documents(q.query)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query.")


@app.delete("/clear")
def clear_documents():
    """Remove all uploaded documents and reset the knowledge base."""
    clear_all_documents()
    return {"message": "All documents cleared. Knowledge base reset."}