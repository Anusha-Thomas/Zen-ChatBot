from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os, time

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://www.zeninstitute.in/")

# Build RAG pipeline at import time (can be heavy — fine for single-instance)
loader = WebBaseLoader(WEBSITE_URL)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100,
                                         separators=["\n\n", "\n", " ", ""])
chunks = splitter.split_documents(docs)

embedding = HuggingFaceBgeEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
texts = [doc.page_content for doc in chunks]
vectorstore = FAISS.from_texts(texts, embedding)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

prompt = PromptTemplate(
    template="""
You are the official assistant for Zen Institute. Answer using ONLY the context below. If the exact answer is not contained, say you are not fully sure and suggest contacting the institute.

Context:
{context}

Question:
{question}

Answer:
""",
    input_variables=["context", "question"],
)

llm = None
if GOOGLE_API_KEY:
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)

qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever, chain_type_kwargs={"prompt": prompt})

FEE_KEYWORDS = ["fee","fees","cost","price","payment","admission","tuition","how much"]
COURSE_KEYWORDS = ["course","courses","program","training","class","syllabus","curriculum","duration"]

def is_fee_question(text: str) -> bool:
    q = (text or "").lower()
    return any(k in q for k in FEE_KEYWORDS)

def is_course_question(text: str) -> bool:
    q = (text or "").lower()
    return any(k in q for k in COURSE_KEYWORDS)

def rag_answer(question: str) -> str:
    try:
        if hasattr(qa_chain, "run"):
            out = qa_chain.run(question)
            if isinstance(out, str):
                return out
            if isinstance(out, dict):
                return out.get("result") or out.get("answer") or ""
        elif hasattr(qa_chain, "invoke"):
            r = qa_chain.invoke({"query": question})
            if isinstance(r, dict):
                return r.get("result") or r.get("answer") or ""
            return str(r)
    except Exception as e:
        print("RAG error:", e)
    return ""

def llm_fallback(question: str) -> str:
    if llm is None:
        return ""
    try:
        if hasattr(llm, "invoke"):
            r = llm.invoke(question)
            if isinstance(r, dict):
                return r.get("content") or r.get("text") or str(r)
            return getattr(r, "content", getattr(r, "text", str(r)))
    except Exception as e:
        print("LLM error:", e)
    return ""

def smart_qa(question: str) -> str:
    rag = rag_answer(question)
    low = (rag or "").lower()
    if rag and not ("not contain" in low or "not available" in low or "i am not sure" in low):
        return rag
    fallback = llm_fallback(question)
    if fallback:
        return fallback
    return "I am not fully sure based on the available information. Please fill the contact form and our team will help you."

# Export
qa = smart_qa
