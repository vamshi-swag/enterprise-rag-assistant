from urllib import response

from fastapi import FastAPI, UploadFile, File
import shutil
from backend.rag import create_rag_pipeline
rag_pipeline = None

app = FastAPI()


current_file = None


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global rag_pipeline

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rag_pipeline = create_rag_pipeline(file_path)

    return {"message": "File uploaded and processed"}


@app.post("/chat")
async def chat(query: str):
    global rag_pipeline

    if rag_pipeline is None:
        return {"error": "Upload document first"}

    response = rag_pipeline(query)

    return response

@app.get("/")
def home():
    return {"message": "RAG API is running 🚀"}