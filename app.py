import streamlit as st
import os
import json
from datetime import datetime, timedelta
import pyodbc
from dotenv import load_dotenv
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.output_parsers import StrOutputParser
from internet_search import internet_search

load_dotenv()

# Global variables
EMBED_DIR = "research_papers"

# === FAISS Document Setup ===
def create_faiss_retriever():
    if "vectors" not in st.session_state:
        embeddings = OllamaEmbeddings(model="all-minilm:latest")
        loader = PyPDFDirectoryLoader(EMBED_DIR)
        raw_docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(raw_docs)
        vectorstore = FAISS.from_documents(docs, embeddings)
        st.session_state.vectors = vectorstore
        st.session_state.retriever = vectorstore.as_retriever()

# === Unified Prompt Template ===
prompt = ChatPromptTemplate.from_template(
    """
   You are a Zimbabwean legal expert assistant. Follow these rules STRICTLY:
1. ANSWER ONLY USING THE PROVIDED DOCUMENTS
2. NEVER use outside knowledge or make assumptions
3. If unsure, say: "This specific provision isn't clear in the documents I have."
4. For incomplete information: "The documents don't fully address this question."
5. ALWAYS reference the exact document source in your answer
6. IF AND ONLY IF no relevant information exists in the documents AND no database information exists, you MUST begin your response with: "I couldn't find relevant information in your documents or database. Based on my general knowledge:"
7. THEN provide the most accurate legal information you know.
8.IF AND ONLY IF no relevant information exists in the documents and general knowledge information is not current according to the requested information , you MUST begin your response with: After Checking the internet:" 
9. THEN provide the most accurate and upto date  information from the internet know.
                 
 Never mix document information with general knowledge. If documents exist, use ONLY those. If no documents match, use ONLY general knowledge and always include the required preface.

    <context>
    {context}
    </context>
    QUESTION: {input}
    """
)

# === SQL Server Functions ===
def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        "DATABASE=Genai;"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str, timeout=10)

def authenticate_user(emp_id, surname):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, surname FROM employees WHERE id = ? AND surname = ?", (emp_id, surname))
        result = cursor.fetchone()
        return {"id": result[0], "name": result[1]} if result else None
    finally:
        conn.close()

def query_employee_data(emp_id, query):
    keywords = query.lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT surname, vacation_days, position, department, hire_date FROM employees WHERE id = ?", (emp_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        surname, vacation_days, position, department, hire_date = result
        if "vacation" in keywords or "leave" in keywords:
            return f"{surname}, you have {vacation_days} vacation days left."
        elif "position" in keywords:
            return f"{surname}, your current position is {position}."
        elif "department" in keywords:
            return f"{surname}, you are in the {department} department."
        elif "hire date" in keywords:
            return f"{surname}, your hire date is {hire_date}."
    return None

def save_chat_history(emp_id: str, messages: list, hours: int = 24):
    conn = get_connection()
    try:
        expires = datetime.now() + timedelta(hours=hours)
        cursor = conn.cursor()
        cursor.execute("""
            MERGE INTO chat_history AS target
            USING (SELECT ? AS emp_id) AS source
            ON target.emp_id = source.emp_id
            WHEN MATCHED THEN UPDATE SET messages = ?, expires_at = ?
            WHEN NOT MATCHED THEN INSERT (emp_id, messages, expires_at)
            VALUES (?, ?, ?);
        """, (emp_id, json.dumps(messages), expires, emp_id, json.dumps(messages), expires))
        conn.commit()
    finally:
        conn.close()

def load_chat_history(emp_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE expires_at < GETDATE()")
        conn.commit()
        cursor.execute("SELECT messages FROM chat_history WHERE emp_id = ?", emp_id)
        result = cursor.fetchone()
        return json.loads(result[0]) if result else []
    finally:
        conn.close()

def clear_chat_history(emp_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE emp_id = ?", emp_id)
        conn.commit()
    finally:
        conn.close()

# === Hybrid Response Generator ===
def generate_response(question: str):
    emp_id = st.session_state.user["id"]

    # 1. Employee DB
    emp_response = query_employee_data(emp_id, question)
    if emp_response:
        return emp_response, "[Source: Employee Records]"

    # 2. Documents
    if "retriever" in st.session_state:
        doc_chain = create_stuff_documents_chain(Ollama(model=st.session_state.llm_model), prompt)
        retrieval_chain = create_retrieval_chain(st.session_state.retriever, doc_chain)
        result = retrieval_chain.invoke({"input": question})
        if result.get("answer") and "don't fully address" not in result["answer"]:
            return result["answer"], "[Source: Legal Documents]"

    # 3. Internet
    if st.session_state.force_web:
        web_result = internet_search(question)
        if web_result:
            return web_result, "[Source: Internet]"

    # 4. Fallback
    return "I'm sorry, I couldn't find any relevant information in the available sources.", "[Source: Not Found]"

# === Streamlit UI ===
st.set_page_config("Hybrid Chatbot", layout="centered")
st.title("💼 Hybrid Knowledge Chatbot")

if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm_model" not in st.session_state:
    st.session_state.llm_model = "mistral"
if "force_web" not in st.session_state:
    st.session_state.force_web = False

# Login UI
if not st.session_state.user:
    st.subheader("🔐 Employee Login")
    with st.form("login"):
        emp_id = st.text_input("Employee ID")
        surname = st.text_input("Surname")
        login = st.form_submit_button("Login")
        if login:
            user = authenticate_user(emp_id, surname)
            if user:
                st.session_state.user = user
                st.session_state.messages = load_chat_history(user["id"])
                create_faiss_retriever()
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
else:
    # Main App
    st.sidebar.header("Settings")
    st.session_state.llm_model = st.sidebar.selectbox("LLM Model", ["mistral", "gemma:2b", "llama2:latest"], 0)
    st.session_state.force_web = st.sidebar.checkbox("🌐 Force Internet Search")
    retention = st.sidebar.slider("Chat Retention (hrs)", 1, 72, 24)
    if st.sidebar.button("🔄 Clear History"):
        clear_chat_history(st.session_state.user["id"])
        st.session_state.messages = []
        st.rerun()
    if st.sidebar.button("🚪 Logout"):
        save_chat_history(st.session_state.user["id"], st.session_state.messages, retention)
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

    # Chat Interface
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_query := st.chat_input("Ask something..."):
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)
        response, source = generate_response(user_query)

        full_reply = f"{response}\n\n{source}"
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
        st.chat_message("assistant").write(full_reply)
        save_chat_history(st.session_state.user["id"], st.session_state.messages, retention)
