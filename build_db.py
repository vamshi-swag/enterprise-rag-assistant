from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

loader = PyPDFLoader("sample.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
split_docs = splitter.split_documents(docs)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectordb = Chroma.from_documents(
    split_docs,
    embeddings,
    persist_directory="db"
)

vectordb.persist()

print("DB created successfully")