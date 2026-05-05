import streamlit as st
import requests
import os
import time

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Knowledge Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
}
.stApp { background-color: #212121; color: #ececec; }
[data-testid="stSidebar"] { background-color: #171717; border-right: 1px solid #2f2f2f; }
[data-testid="stSidebar"] * { color: #ececec !important; }
.sidebar-title { font-size:13px; font-weight:600; color:#8e8ea0 !important; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:12px; padding:0 4px; }
.doc-pill { display:flex; align-items:center; gap:8px; background:#2a2a2a; border:1px solid #3a3a3a; border-radius:8px; padding:8px 12px; margin-bottom:6px; font-size:13px; color:#ececec; }
.doc-pill-name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
.doc-pill-chunks { font-size:11px; color:#8e8ea0; flex-shrink:0; }
.status-badge { display:inline-flex; align-items:center; gap:6px; padding:5px 10px; border-radius:20px; font-size:12px; font-weight:500; margin-bottom:12px; }
.status-online { background:#1a3a2a; border:1px solid #2d6a4f; color:#52b788; }
.status-offline { background:#3a1a1a; border:1px solid #6a2d2d; color:#e07070; }
.status-empty { background:#2a2a1a; border:1px solid #5a5a2d; color:#b8b852; }
[data-testid="stFileUploader"] { background:#2a2a2a; border:1.5px dashed #3f3f3f; border-radius:12px; padding:8px; }
.stButton > button { background:#7c6ff7 !important; color:#ffffff !important; border:none !important; border-radius:8px !important; font-weight:500 !important; font-size:14px !important; width:100%; }
.stButton > button:hover { background:#6c5fe6 !important; }
.clear-btn button { background:transparent !important; color:#8e8ea0 !important; border:1px solid #3f3f3f !important; font-size:13px !important; }
.clear-btn button:hover { background:#3a1a1a !important; color:#e07070 !important; border-color:#6a2d2d !important; }
.main-header { text-align:center; padding:40px 0 20px; }
.main-title { font-size:28px; font-weight:700; color:#ececec; margin:0; }
.main-subtitle { font-size:14px; color:#8e8ea0; margin-top:6px; }
.empty-state { text-align:center; padding:60px 20px; }
.empty-icon { font-size:48px; margin-bottom:16px; }
.empty-title { font-size:18px; font-weight:600; color:#ececec; margin-bottom:8px; }
.empty-desc { font-size:14px; color:#8e8ea0; max-width:340px; margin:0 auto; line-height:1.6; }
.source-card { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; padding:8px 12px; background:#2a2a2a; border:1px solid #3a3a3a; border-radius:8px; }
.source-tag { background:#1a2a3a; border:1px solid #2d4a6a; color:#7cb9e8; border-radius:4px; padding:2px 8px; font-size:11px; }
.page-tag { background:#1a3a2a; border:1px solid #2d6a4f; color:#52b788; border-radius:4px; padding:2px 8px; font-size:11px; }
.chunk-tag { background:#2a1a3a; border:1px solid #4f2d6a; color:#b888e0; border-radius:4px; padding:2px 8px; font-size:11px; }
[data-testid="stChatInput"] { background:#2f2f2f !important; border:1px solid #3f3f3f !important; border-radius:16px !important; }
[data-testid="stChatInput"]:focus-within { border-color:#7c6ff7 !important; }
#MainMenu, footer, header { visibility:hidden; }
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:#212121; }
::-webkit-scrollbar-thumb { background:#3f3f3f; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_loaded" not in st.session_state:
    st.session_state.document_loaded = False
if "all_docs" not in st.session_state:
    st.session_state.all_docs = {}

def get_health():
    try:
        res = requests.get(f"{API_URL}/health", timeout=3)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 20px;">
        <div style="font-size:22px;font-weight:700;color:#ececec;">🧠 RAG Assistant</div>
        <div style="font-size:12px;color:#8e8ea0;margin-top:3px;">Multi-document knowledge base</div>
    </div>
    """, unsafe_allow_html=True)

    health = get_health()
    if health is None:
        st.markdown('<div class="status-badge status-offline">🔴 API offline</div>', unsafe_allow_html=True)
    elif health.get("documents_loaded", 0) > 0:
        n = health["documents_loaded"]
        st.markdown(f'<div class="status-badge status-online">🟢 {n} document{"s" if n>1 else ""} loaded</div>', unsafe_allow_html=True)
        st.session_state.document_loaded = True
    else:
        st.markdown('<div class="status-badge status-empty">🟡 No documents yet</div>', unsafe_allow_html=True)
        st.session_state.document_loaded = False

    st.markdown('<div class="sidebar-title">Upload Documents</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Drop a PDF here", type="pdf", label_visibility="collapsed")

    if uploaded_file:
        if st.button("➕ Add to Knowledge Base", use_container_width=True):
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    res = requests.post(f"{API_URL}/upload", files=files, timeout=120)
                    if res.status_code == 200:
                        data = res.json()
                        chunks = data.get("chunks_added", 0)
                        st.session_state.all_docs[uploaded_file.name] = chunks
                        st.session_state.document_loaded = True
                        st.success(f"✅ Added — {chunks} chunks indexed")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error(f"❌ {res.json().get('detail', 'Upload failed')}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to backend")
                except requests.exceptions.Timeout:
                    st.error("❌ Timed out — try a smaller PDF")
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    if health and health.get("files"):
        st.markdown('<div class="sidebar-title" style="margin-top:20px;">Knowledge Base</div>', unsafe_allow_html=True)
        for fname in health["files"]:
            chunks = st.session_state.all_docs.get(fname, "?")
            short = fname if len(fname) <= 24 else fname[:21] + "..."
            st.markdown(f"""
            <div class="doc-pill">
                <span>📄</span>
                <span class="doc-pill-name" title="{fname}">{short}</span>
                <span class="doc-pill-chunks">{chunks} chunks</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        if st.button("🗑️ Clear All Documents", use_container_width=True):
            try:
                res = requests.delete(f"{API_URL}/clear", timeout=10)
                if res.status_code == 200:
                    st.session_state.messages = []
                    st.session_state.document_loaded = False
                    st.session_state.all_docs = {}
                    st.rerun()
            except Exception as e:
                st.error(f"❌ {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:32px;font-size:11px;color:#4f4f4f;line-height:1.8;">
        LangChain · ChromaDB · Groq LLM<br>FastAPI · Streamlit
    </div>""", unsafe_allow_html=True)

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">RAG Knowledge Assistant</div>
    <div class="main-subtitle">Ask anything across your uploaded documents</div>
</div>""", unsafe_allow_html=True)

if not st.session_state.document_loaded:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">📚</div>
        <div class="empty-title">Your knowledge base is empty</div>
        <div class="empty-desc">Upload one or more PDFs from the sidebar. Then ask questions across all of them at once.</div>
    </div>""", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            sources_html = "".join([f'<span class="source-tag">📁 {s}</span>' for s in msg.get("sources", [])])
            pages_html = "".join([f'<span class="page-tag">p.{p}</span>' for p in msg.get("pages", [])])
            chunks_html = f'<span class="chunk-tag">🔍 {msg.get("chunks", 0)} chunks</span>'
            st.markdown(f'<div class="source-card">{sources_html}{pages_html}{chunks_html}</div>', unsafe_allow_html=True)

prompt = st.chat_input(
    "Message RAG Assistant..." if st.session_state.document_loaded else "Upload a PDF to start...",
    disabled=not st.session_state.document_loaded,
)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        thinking = st.empty()
        for dots in ["Thinking", "Thinking.", "Thinking..", "Thinking..."]:
            thinking.markdown(f"<span style='color:#8e8ea0;font-size:14px;'>{dots}</span>", unsafe_allow_html=True)
            time.sleep(0.3)

        try:
            res = requests.post(f"{API_URL}/chat", json={"query": prompt}, timeout=60)
            thinking.empty()

            if res.status_code == 200:
                data = res.json()
                answer = data.get("answer", "No answer returned.")
                sources = data.get("sources", [])
                pages = data.get("pages_referenced", [])
                chunks = data.get("chunks_used", 0)

                # Word-by-word typing effect
                box = st.empty()
                displayed = ""
                for word in answer.split(" "):
                    displayed += word + " "
                    box.markdown(displayed + "▌")
                    time.sleep(0.015)
                box.markdown(answer)

                if sources:
                    sources_html = "".join([f'<span class="source-tag">📁 {s}</span>' for s in sources])
                    pages_html = "".join([f'<span class="page-tag">p.{p}</span>' for p in pages])
                    chunks_html = f'<span class="chunk-tag">🔍 {chunks} chunks</span>'
                    st.markdown(f'<div class="source-card">{sources_html}{pages_html}{chunks_html}</div>', unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "pages": pages,
                    "chunks": chunks,
                })

            elif res.status_code == 400:
                st.error(f"❌ {res.json().get('detail', 'Bad request')}")
            else:
                st.error(f"❌ API error {res.status_code}")

        except requests.exceptions.ConnectionError:
            thinking.empty()
            st.error("❌ Cannot reach the backend. Is uvicorn running?")
        except requests.exceptions.Timeout:
            thinking.empty()
            st.error("❌ Request timed out.")
        except Exception as e:
            thinking.empty()
            st.error(f"❌ {str(e)}")