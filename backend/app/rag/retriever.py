"""Retrieval-augmented generation: retrieve top-k chunks and answer with the LLM."""

from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.ingestion.embedder import get_embedding_model
from app.models.schemas import ChatResponse
from app.rag.vectorstore import load_vectorstore

SYSTEM_PROMPT = (
    "Answer only using the provided context. "
    "If the context doesn't contain the answer, say you don't know."
)

MODEL_NAME = "llama-3.1-8b-instant"
TOP_K = 3

_llm = ChatGroq(model=MODEL_NAME)
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("system", "Context:\n{context}"),
        ("human", "{question}"),
    ]
)


async def get_answer(query: str) -> ChatResponse:
    """Asynchronously retrieve top-k chunks for *query* and generate an answer.

    Uses the vectorstore's async API and an async LLM call so the event loop
    stays free and concurrent requests are not serialized.
    """
    vectorstore = load_vectorstore(get_embedding_model())
    docs = await vectorstore.asimilarity_search(query, k=TOP_K)

    context = "\n\n".join(doc.page_content for doc in docs)
    sources = list(
        dict.fromkeys(
            Path(doc.metadata.get("source", "unknown")).name for doc in docs
        )
    )

    result = await (_prompt | _llm).ainvoke({"context": context, "question": query})
    return ChatResponse(answer=result.content, sources=sources)
