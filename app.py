import os
import streamlit as st

from pdf_reader import extract_pdf_pages
from retriever import VectorlessRetriever
from memory import (
    init_db,
    create_chat,
    get_chats,
    save_message,
    get_messages,
    get_recent_history,
    update_chat_name,
    get_chat_name,
    delete_chat
)
from llm_answer import generate_answer


init_db()

st.set_page_config(
    page_title="DocMind",
    page_icon="📄",
    layout="wide"
)


# -----------------------------
# CUSTOM UI STYLING
# -----------------------------
# -----------------------------
# CUSTOM UI STYLING
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: #f7f9fc;
        color: #111827;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] * {
        color: #111827 !important;
    }

    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #111827;
    }

    .stChatMessage {
        border-radius: 16px;
        padding: 12px;
        margin-bottom: 12px;
        background: #ffffff;
        color: #111827;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }

    .stChatMessage * {
        color: #111827 !important;
    }

    .stButton button {
        border-radius: 10px;
        border: 1px solid #d1d5db;
        background: #ffffff;
        color: #111827 !important;
        font-weight: 500;
    }

    .stButton button:hover {
        border-color: #2563eb;
        color: #2563eb !important;
    }

    .stTextInput input {
        border-radius: 10px;
        color: #111827 !important;
        background: #ffffff !important;
    }

    [data-testid="stExpander"] {
        background: #ffffff;
        color: #111827;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }

    [data-testid="stExpander"] * {
        color: #111827 !important;
    }

    .stAlert {
        border-radius: 14px;
        color: #111827;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)
# -----------------------------
# SESSION STATE
# -----------------------------
if "retriever" not in st.session_state:
    st.session_state.retriever = VectorlessRetriever()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_loaded" not in st.session_state:
    st.session_state.pdf_loaded = False

if "uploaded_pdf_names" not in st.session_state:
    st.session_state.uploaded_pdf_names = []

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

if "current_chat_id" not in st.session_state:
    chats = get_chats()

    if chats:
        st.session_state.current_chat_id = chats[0][0]
        saved_messages = get_messages(chats[0][0])
        st.session_state.messages = [
            {"role": role, "content": content}
            for role, content in saved_messages
        ]
    else:
        new_chat_id = create_chat("New Chat")
        st.session_state.current_chat_id = new_chat_id
        st.session_state.messages = []


# -----------------------------
# HEADER
# -----------------------------
st.title("📄 DocMind")
st.caption(
    "Vectorless RAG PDF Chatbot with Groq LLM, PDF Selection, Multi-Chat Memory, and Source Preview"
)

current_chat_name = get_chat_name(st.session_state.current_chat_id)
st.info(f"🟢 Current Chat: {current_chat_name}")


# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.header("💬 Chats")

    if st.button("➕ New Chat"):
        new_chat_id = create_chat("New Chat")
        st.session_state.current_chat_id = new_chat_id
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.rerun()

    chats = get_chats()

    for chat_id, chat_name in chats:
        label = f"💬 {chat_name} #{chat_id}"

        if st.button(label, key=f"chat_{chat_id}"):
            st.session_state.current_chat_id = chat_id

            saved_messages = get_messages(chat_id)
            st.session_state.messages = [
                {"role": role, "content": content}
                for role, content in saved_messages
            ]

            st.session_state.last_sources = []
            st.rerun()

    st.divider()

    st.subheader("⚙️ Chat Settings")

    rename_value = st.text_input(
        "Rename current chat",
        value=get_chat_name(st.session_state.current_chat_id)
    )

    if st.button("✏️ Rename Chat"):
        if rename_value.strip():
            update_chat_name(
                st.session_state.current_chat_id,
                rename_value.strip()
            )
            st.rerun()
        else:
            st.warning("Chat name cannot be empty.")

    if st.button("🗑️ Delete Current Chat"):
        delete_chat(st.session_state.current_chat_id)

        remaining_chats = get_chats()

        if remaining_chats:
            next_chat_id = remaining_chats[0][0]
            st.session_state.current_chat_id = next_chat_id

            saved_messages = get_messages(next_chat_id)
            st.session_state.messages = [
                {"role": role, "content": content}
                for role, content in saved_messages
            ]
        else:
            new_chat_id = create_chat("New Chat")
            st.session_state.current_chat_id = new_chat_id
            st.session_state.messages = []

        st.session_state.last_sources = []
        st.rerun()

    st.divider()

    st.header("📂 Upload PDFs")

    uploaded_files = st.file_uploader(
        "Upload one or more PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("Process PDFs"):
        if uploaded_files:
            os.makedirs("uploads", exist_ok=True)

            all_pages = []
            uploaded_names = []

            with st.spinner("Reading and indexing PDFs..."):
                for file in uploaded_files:
                    file_path = os.path.join("uploads", file.name)

                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())

                    pages = extract_pdf_pages(file_path, file.name)

                    all_pages.extend(pages)
                    uploaded_names.append(file.name)

                st.session_state.retriever.build_index(all_pages)
                st.session_state.pdf_loaded = True
                st.session_state.uploaded_pdf_names = uploaded_names
                st.session_state.selected_files = uploaded_names

            st.success(f"Successfully indexed {len(uploaded_files)} PDF(s)")
            st.info(f"Total pages indexed: {len(all_pages)}")
        else:
            st.warning("Please upload at least one PDF.")

    st.divider()

    st.subheader("📄 Uploaded Files")

    if st.session_state.uploaded_pdf_names:
        for pdf_name in st.session_state.uploaded_pdf_names:
            st.write(f"✅ {pdf_name}")

        st.session_state.selected_files = st.multiselect(
            "Choose PDFs to search",
            options=st.session_state.uploaded_pdf_names,
            default=st.session_state.selected_files
        )
    else:
        st.write("No PDFs uploaded yet.")

    st.divider()

    if st.button("🧹 Clear Current Chat Screen"):
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.rerun()


# -----------------------------
# MAIN LAYOUT
# -----------------------------
chat_col, source_col = st.columns([2, 1])


# -----------------------------
# CHAT AREA
# -----------------------------
with chat_col:
    st.subheader("💬 Chat")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask a question from your uploaded PDFs...")

    if question:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        save_message(
            st.session_state.current_chat_id,
            "user",
            question
        )

        current_chat_name = get_chat_name(st.session_state.current_chat_id)

        if current_chat_name == "New Chat":
            update_chat_name(
                st.session_state.current_chat_id,
                question[:35]
            )

        with st.chat_message("user"):
            st.markdown(question)

        if not st.session_state.pdf_loaded:
            answer = "⚠️ Please upload and process PDF files first."
            st.session_state.last_sources = []

        elif not st.session_state.selected_files:
            answer = "⚠️ Please select at least one PDF to search."
            st.session_state.last_sources = []

        else:
            results = st.session_state.retriever.search(
                question,
                top_k=3,
                selected_files=st.session_state.selected_files
            )

            st.session_state.last_sources = results

            if len(results) == 0:
                answer = (
                    "❌ I could not find relevant information "
                    "inside the selected PDFs."
                )
            else:
                history = get_recent_history(
                    st.session_state.current_chat_id,
                    limit=5
                )

                with st.spinner("Generating answer..."):
                    answer = generate_answer(
                        question,
                        results,
                        history
                    )

                sources = "\n\n### 📌 Sources\n"

                for page in results:
                    sources += (
                        f"- 📄 **{page['file_name']}** — "
                        f"Page {page['page_number']}\n"
                    )

                answer = answer + sources

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        save_message(
            st.session_state.current_chat_id,
            "assistant",
            answer
        )

        with st.chat_message("assistant"):
            st.markdown(answer)


# -----------------------------
# SOURCE PREVIEW PANEL
# -----------------------------
with source_col:
    st.subheader("📌 Source Preview")

    if st.session_state.last_sources:
        for idx, page in enumerate(st.session_state.last_sources, start=1):
            with st.expander(
                f"Source {idx}: {page['file_name']} — Page {page['page_number']}",
                expanded=(idx == 1)
            ):
                preview_text = page["text"][:1500]

                st.markdown(f"**PDF:** {page['file_name']}")
                st.markdown(f"**Page:** {page['page_number']}")
                st.markdown("**Preview:**")
                st.write(preview_text)

                if len(page["text"]) > 1500:
                    st.caption("Preview shortened. Full page text is longer.")
    else:
        st.info("Ask a question to see source pages here.")