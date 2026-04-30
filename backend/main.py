from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
from backend.rag import create_rag_pipeline

app = FastAPI()

rag_pipeline = None  # lazy load

class Query(BaseModel):
    query: str

@app.get("/")
def home():
    return {"message": "RAG API is running 🚀"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global rag_pipeline

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ Build RAG ONLY when needed (fix memory crash)
    rag_pipeline = create_rag_pipeline(file_path)

    return {"message": "File processed"}

@app.post("/chat")
async def chat(q: Query):
    global rag_pipeline

    if rag_pipeline is None:
        return {"error": "Upload document first"}

    result = rag_pipeline(q.query)

    return result