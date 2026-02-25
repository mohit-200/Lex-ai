"""
RAG Query Engine.

This is the core of LegalDoc AI. It:
1. Retrieves semantically relevant clauses from Qdrant
2. Checks confidence before answering (key differentiator)
3. Generates a grounded answer with exact source citations
4. Logs every query for later RAGAS evaluation
"""
import time
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.vector_store import search
from app.models.schemas import QueryResponse, SourceClause

client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """You are a precise legal document analyst. Your job is to answer questions 
about legal contracts based ONLY on the provided document clauses.

Rules you must follow:
1. Only use information from the provided clauses. Never invent or infer beyond them.
2. Always cite the specific clause or section you're drawing from.
3. If the clauses don't contain enough information to answer confidently, say so explicitly.
4. Use plain English — avoid unnecessary legal jargon unless quoting directly.
5. If something is ambiguous or has legal implications, say so and recommend consulting a lawyer.

Format your answer as:
- A direct answer to the question (2-4 sentences)
- Key clause references that support your answer
"""

LOW_CONFIDENCE_RESPONSE = (
    "The document doesn't contain a clear clause addressing this specific question. "
    "The closest relevant sections are shown in the sources below, but you should "
    "verify this manually or consult a legal professional."
)


async def query_document(
    document_id: str,
    query: str,
    top_k: int = 6,
) -> QueryResponse:
    start_time = time.time()

    # Step 1: Retrieve relevant clauses
    results = await search(document_id, query, top_k=top_k)

    if not results:
        return QueryResponse(
            answer="No relevant clauses found in this document for your query.",
            confidence=0.0,
            is_confident=False,
            sources=[],
            latency_ms=int((time.time() - start_time) * 1000),
        )

    # Step 2: Calculate confidence from retrieval scores
    # Qdrant cosine similarity scores range 0-1
    top_score = results[0].score
    avg_top3_score = sum(r.score for r in results[:3]) / min(3, len(results))
    confidence = round((top_score * 0.6 + avg_top3_score * 0.4), 3)
    is_confident = confidence >= settings.confidence_threshold

    # Step 3: Build context from retrieved clauses
    context_parts = []
    for i, result in enumerate(results, 1):
        payload = result.payload
        clause_ref = f"[Clause {payload.get('clause_number', 'N/A')} | Page {payload.get('page', '?')}]"
        context_parts.append(f"{clause_ref}\n{payload['text']}")

    context = "\n\n---\n\n".join(context_parts)

    # Step 4: Generate answer — but be honest if confidence is low
    if is_confident:
        user_prompt = f"""Document clauses:

{context}

Question: {query}

Answer based strictly on the clauses above."""
    else:
        # Still retrieve and show sources, but frame answer differently
        user_prompt = f"""Document clauses (low relevance match — answer with caution):

{context}

Question: {query}

Note: The retrieved clauses have low relevance scores. If you cannot find a clear answer, 
say so explicitly rather than guessing."""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,   # Low temp for factual, consistent answers
        max_tokens=600,
    )

    answer = response.choices[0].message.content.strip()

    # If not confident, prepend a clear warning
    if not is_confident:
        answer = f"⚠️ Low confidence: {LOW_CONFIDENCE_RESPONSE}\n\n{answer}"

    # Step 5: Build source citations
    sources = [
        SourceClause(
            text=result.payload["text"][:300] + "..." if len(result.payload["text"]) > 300 else result.payload["text"],
            page=result.payload.get("page", 0),
            clause_number=result.payload.get("clause_number"),
            similarity_score=round(result.score, 3),
        )
        for result in results
    ]

    latency_ms = int((time.time() - start_time) * 1000)

    return QueryResponse(
        answer=answer,
        confidence=confidence,
        is_confident=is_confident,
        sources=sources,
        latency_ms=latency_ms,
    )
