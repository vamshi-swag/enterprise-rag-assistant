# Enterprise RAG Knowledge Assistant

An end-to-end Retrieval-Augmented Generation (RAG) system that lets
users ask natural language questions about any PDF document and receive
accurate, context-aware answers — powered by LLMs and semantic search.

---

## The Problem It Solves

Teams waste hours manually searching through large documents, reports,
and PDFs. This system makes any document instantly queryable through
natural language — no search keywords, no manual reading, just ask and
get answers with page references.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq — Llama 3.1 8B Instant |
| Orchestration | LangChain |
| Vector Database | ChromaDB |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Backend API | FastAPI |
| Frontend | Streamlit |

---

## System Architecture

```
User Query
    ↓
Streamlit Frontend
    ↓
FastAPI Backend (/chat endpoint)
    ↓
Query Embedding (HuggingFace)
    ↓
Semantic Search — ChromaDB (k=3 chunks)
    ↓
Context Assembly
    ↓
Groq LLM — Llama 3.1 8B
    ↓
Answer + Page References → User
```

---

## How To Run Locally

### 1. Clone the repository
```bash
git clone https://github.com/vamshi-swag/rag-app
cd rag-app
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
```bash
cp .env.example .env
# Add your Groq API key inside .env
```

### 4. Start the backend
```bash
uvicorn backend.main:app --reload
```

### 5. Start the frontend (new terminal)
```bash
streamlit run frontend/app.py
```

### 6. Open your browser
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | / | Health check |
| GET | /health | Document load status |
| POST | /upload | Upload and process a PDF |
| POST | /chat | Ask a question |

---

## Key Technical Decisions

**Why ChromaDB?**
Lightweight, runs locally without a managed cloud service — ideal for
prototyping and small-to-medium document collections.

**Why chunk_size=512 with 64 overlap?**
512 tokens gives the LLM enough context per chunk to form meaningful
answers. The 64-token overlap preserves context at chunk boundaries —
critical for questions that span paragraph breaks.

**Why k=3?**
Fetching 3 relevant chunks gives the LLM enough context diversity
to answer multi-part questions without exceeding token limits.

**Why temperature=0.2?**
Lower temperature makes the model more factual and less likely to
hallucinate content not present in the retrieved context.

---

## What I Learned Building This

- Chunk size directly impacts answer quality — too small loses context,
  too large reduces retrieval precision
- Embedding model choice matters more than vector DB choice for accuracy
- FastAPI async endpoints handle concurrent document queries efficiently
- Always clean up temp files — file leaks crash production servers
- Proper error handling in the frontend prevents silent failures

---

## Roadmap

- [ ] Multi-document support — query across multiple PDFs at once
- [ ] Conversation memory — maintain context across multiple questions
- [ ] Hybrid search — combine vector + keyword search for better recall
- [ ] Azure AI Search integration for enterprise scale
- [ ] Evaluation metrics — faithfulness and relevancy scoring
- [ ] Docker compose for one-command local setup

---

## Author

**Vamshi Neelakantam**
Generative AI Engineer · Hyderabad, India
[LinkedIn](https://linkedin.com/in/vamshi-neelakantam) ·
[GitHub](https://github.com/vamshi-swag) ·
nvamshi630@gmail.com
