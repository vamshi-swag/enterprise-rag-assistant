from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat_history = []

def generate_answer(query, context):
    global chat_history

    chat_history.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Answer based on context."},
            *chat_history,
            {"role": "user", "content": f"Context:\n{context}"}
        ]
    )

    answer = response.choices[0].message.content

    chat_history.append({"role": "assistant", "content": answer})

    return answer


def create_rag_pipeline(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings()

    vectordb = Chroma.from_documents(split_docs, embeddings)
    retriever = vectordb.as_retriever()

    def rag_pipeline(query):
        docs = retriever.get_relevant_documents(query)

        context = "\n".join([doc.page_content for doc in docs])
        sources = [doc.metadata.get("source", "unknown") for doc in docs]

        answer = generate_answer(query, context)

        return {
            "answer": answer,
            "sources": list(set(sources))
        }

    return rag_pipeline