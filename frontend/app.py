import streamlit as st
import requests

# 🔥 CHANGE THIS AFTER DEPLOYMENT
API_URL = "https://YOUR-RENDER-APP.onrender.com"

st.set_page_config(page_title="RAG AI", layout="wide")
st.title("🤖 RAG AI Assistant")

# memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# upload
uploaded_file = st.file_uploader("📄 Upload PDF", type="pdf")

if uploaded_file:
    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
    res = requests.post(f"{API_URL}/upload", files=files)
    if res.status_code == 200:
        st.success("File uploaded & processed!")
    else:
        st.error("Upload failed")

# chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# input
prompt = st.chat_input("Ask something...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    res = requests.post(
        f"{API_URL}/chat",
        json={"query": prompt}
    )

    data = res.json()

    answer = data.get("answer", "No response")
    sources = data.get("sources", [])

    with st.chat_message("assistant"):
        st.write(answer)

        if sources:
            st.caption("📚 Sources: " + ", ".join(sources))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })