from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
from groq import Groq
import gc

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_answer(query, context):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Answer ONLY based on context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )
    return response.choices[0].message.content


def create_rag_pipeline(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # ✅ LIMIT DOC SIZE (critical for memory)
    docs = docs[:15]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20
    )
    split_docs = splitter.split_documents(docs)

    # ✅ CPU-only lightweight embedding
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    vectordb = Chroma.from_documents(split_docs, embeddings)

    retriever = vectordb.as_retriever(search_kwargs={"k": 1})

    def rag_pipeline(query):
        docs = retriever.get_relevant_documents(query)

        context = "\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get("source", "unknown") for doc in docs]

        answer = generate_answer(query, context)

        return {
            "answer": answer,
            "sources": list(set(sources))
        }

    # ✅ free memory after setup
    gc.collect()

    return rag_pipeline