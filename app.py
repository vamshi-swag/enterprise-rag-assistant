import streamlit as st
import requests

st.set_page_config(page_title="RAG AI", layout="wide")

st.title("🤖 RAG AI Assistant")

# Memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Upload
uploaded_file = st.file_uploader("📄 Upload PDF", type="pdf")

if uploaded_file:
    res = requests.post(
        "http://127.0.0.1:8000/upload",
        files={"file": uploaded_file}
    )
    st.success("File uploaded!")

# Chat UI
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input
prompt = st.chat_input("Ask something...")

if prompt:
    # show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)

    # get response
    res = requests.post(
        "http://127.0.0.1:8000/chat",
        params={"query": prompt}
    )

    answer = res.json().get("answer", "")
    sources = res.json().get("sources", [])

    st.write(answer)

    if sources:
        st.caption("Sources: " + ", ".join(sources))

    # show assistant
    with st.chat_message("assistant"):
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})