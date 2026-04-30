from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
import os
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

chat_history = []

def generate_answer(query, context):
    global chat_history

    chat_history.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "Answer ONLY based on provided context."},
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

    # ✅ Reduced memory usage
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30
    )
    split_docs = splitter.split_documents(docs)

    # ✅ Lightweight embeddings (IMPORTANT for Render)
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vectordb = Chroma.from_documents(split_docs, embeddings)

    retriever = vectordb.as_retriever(search_kwargs={"k": 2})  # less memory

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