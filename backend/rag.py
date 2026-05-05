from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
import gc
import logging
from groq import Groq

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Embedding model loaded once at startup — saves memory on repeated uploads
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
)

# Global in-memory vector store — persists across multiple uploads
vectordb = None
uploaded_files_registry = []  # tracks all uploaded filenames


def generate_answer(query: str, context: str) -> str:
    """Call Groq LLM with retrieved context and return the answer string."""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful document assistant. "
                        "Answer ONLY using the provided context. "
                        "If the answer is not in the context, say so clearly. "
                        "Be concise and accurate."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}",
                },
            ],
            max_tokens=512,
            temperature=0.2,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return f"Error generating answer: {str(e)}"


def add_document(file_path: str, filename: str) -> int:
    """
    Load a PDF, chunk it, and ADD it to the shared vector store.
    Returns the number of chunks added.
    Previous documents are preserved — not replaced.
    """
    global vectordb, uploaded_files_registry

    logger.info(f"Loading document: {file_path}")

    loader = PyPDFLoader(file_path)
    docs = loader.load()

    if not docs:
        raise ValueError("Could not extract text from the uploaded PDF.")

    logger.info(f"Loaded {len(docs)} pages from {filename}")

    # Tag each chunk with the original filename for source attribution
    for doc in docs:
        doc.metadata["filename"] = filename

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=64,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    split_docs = splitter.split_documents(docs)
    logger.info(f"Split into {len(split_docs)} chunks")

    if vectordb is None:
        # First document — create the vector store
        vectordb = Chroma.from_documents(split_docs, embeddings)
    else:
        # Additional documents — add to existing vector store
        vectordb.add_documents(split_docs)

    # Track uploaded files
    if filename not in uploaded_files_registry:
        uploaded_files_registry.append(filename)

    gc.collect()
    return len(split_docs)


def query_documents(query: str) -> dict:
    """
    Search across ALL uploaded documents and return a structured answer.
    """
    global vectordb, uploaded_files_registry

    if vectordb is None:
        return {
            "answer": "No documents loaded. Please upload a PDF first.",
            "sources": [],
            "pages_referenced": [],
            "chunks_used": 0,
            "documents_searched": [],
        }

    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3},
    )

    try:
        retrieved_docs = retriever.invoke(query)

        if not retrieved_docs:
            return {
                "answer": "No relevant content found across your uploaded documents.",
                "sources": [],
                "pages_referenced": [],
                "chunks_used": 0,
                "documents_searched": uploaded_files_registry,
            }

        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        # Show which specific files the answer came from
        filenames = list({
            doc.metadata.get("filename", doc.metadata.get("source", "unknown"))
            for doc in retrieved_docs
        })
        pages = list({doc.metadata.get("page", "?") for doc in retrieved_docs})

        answer = generate_answer(query, context)

        return {
            "answer": answer,
            "sources": filenames,
            "pages_referenced": [str(p) for p in sorted(pages)],
            "chunks_used": len(retrieved_docs),
            "documents_searched": uploaded_files_registry,
        }

    except Exception as e:
        logger.error(f"Query error: {e}")
        return {"answer": f"Error processing query: {str(e)}", "sources": []}


def clear_all_documents():
    """Reset the vector store and file registry."""
    global vectordb, uploaded_files_registry
    vectordb = None
    uploaded_files_registry = []
    gc.collect()
    logger.info("All documents cleared.")