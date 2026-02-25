# LegalDoc AI 🏛️

**Production-ready RAG API for legal document intelligence.**

Upload any contract or legal PDF and get:
- ✅ Natural language Q&A with **exact clause citations**
- ✅ Automated **risk detection** (liability, auto-renewal, IP, non-compete, and more)
- ✅ **Contract comparison** with plain-English explanations of what changed
- ✅ **Confidence scoring** — the system tells you when it doesn't know
- ✅ **RAGAS evaluation** pipeline to measure answer quality

---

## Architecture

```
PDF Upload
    │
    ▼
┌─────────────────────────────┐
│  FastAPI Backend             │
│                             │
│  ┌──────────────────────┐   │
│  │ Clause-Aware Parser  │   │  ← PyMuPDF, detects clause boundaries
│  └──────────┬───────────┘   │
│             │               │
│  ┌──────────▼───────────┐   │
│  │ Embedder             │   │  ← OpenAI text-embedding-3-small
│  └──────────┬───────────┘   │
│             │               │
│  ┌──────────▼───────────┐   │
│  │ Qdrant Vector DB     │   │  ← Filtered by document_id
│  └──────────┬───────────┘   │
│             │               │
│  ┌──────────▼───────────┐   │
│  │ RAG Engine + GPT-4o  │   │  ← Confidence-aware generation
│  └──────────────────────┘   │
│                             │
│  ┌──────────────────────┐   │
│  │ Celery + Redis       │   │  ← Async risk analysis job
│  └──────────────────────┘   │
│                             │
│  ┌──────────────────────┐   │
│  │ PostgreSQL           │   │  ← Metadata, logs, risk findings
│  └──────────────────────┘   │
└─────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/legaldoc-ai
cd legaldoc-ai
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 2. Run everything
docker-compose up --build

# 3. API docs available at:
open http://localhost:8000/docs
```

---

## API Endpoints

### Upload a Document
```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@contract.pdf"
```
```json
{
  "document_id": "a1b2c3d4-...",
  "filename": "contract.pdf",
  "page_count": 12,
  "chunk_count": 47,
  "status": "ready",
  "message": "Document indexed. Risk analysis running in background."
}
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/documents/{document_id}/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the payment terms?"}'
```
```json
{
  "answer": "Payment is due within 30 days of invoice (Section 4.2). Late payments incur 1.5% monthly interest per Section 4.3.",
  "confidence": 0.91,
  "is_confident": true,
  "sources": [
    {
      "text": "4.2 Payment Terms. Client shall pay all invoices within thirty (30) days...",
      "page": 5,
      "clause_number": "4.2",
      "similarity_score": 0.94
    }
  ],
  "latency_ms": 1240
}
```

### Get Risk Analysis
```bash
curl http://localhost:8000/documents/{document_id}/risks
```
```json
{
  "document_id": "a1b2c3d4-...",
  "status": "done",
  "overall_risk_score": 6.5,
  "risk_count": 3,
  "risks": [
    {
      "clause_text": "Client shall indemnify Company against any and all claims...",
      "page": 8,
      "risk_type": "indemnification_broad",
      "severity": "high",
      "explanation": "This indemnification clause is one-sided and covers 'any and all' claims with no carve-outs.",
      "recommendation": "Negotiate mutual indemnification or cap liability to direct damages only."
    }
  ]
}
```

### Compare Two Contracts
```bash
curl -X POST http://localhost:8000/compare \
  -F "original=@contract_v1.pdf" \
  -F "revised=@contract_v2.pdf"
```

---

## Key Design Decisions

**Clause-aware chunking** — Unlike most RAG tutorials that split by fixed token windows, this parser respects legal document structure. Clauses stay intact as semantic units, which dramatically improves retrieval quality.

**Confidence scoring** — The system computes a confidence score from Qdrant similarity scores and explicitly tells the user when it isn't confident. Most RAG demos hallucinate confidently. This one doesn't.

**Async risk analysis** — Risk analysis runs as a Celery background job so uploads are fast. The `/risks` endpoint returns the result when ready.

**RAGAS evaluation** — Run `python scripts/evaluate.py` to measure faithfulness, answer relevancy, and context precision. This is what most portfolio projects skip.

---

## Run Evaluations

```bash
# After adding test cases to scripts/evaluate.py
python scripts/evaluate.py
```

Sample output:
```
======================================================
LEGALDOC AI — RAGAS EVALUATION REPORT
======================================================
Metric                    Score      Interpretation
------------------------------------------------------
faithfulness              0.887      ✅ Good
answer_relevancy          0.812      ✅ Good
context_precision         0.743      ✅ Good

Average retrieval confidence: 0.836
Low confidence responses: 1/5
======================================================
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| PDF Parsing | PyMuPDF (fitz) |
| Embeddings | OpenAI text-embedding-3-small |
| Vector DB | Qdrant |
| LLM | GPT-4o |
| Background Jobs | Celery + Redis |
| Database | PostgreSQL + SQLAlchemy |
| Evaluation | RAGAS |
| Containerization | Docker + Docker Compose |
| Testing | pytest + pytest-asyncio |

---

## Project Structure

```
legaldoc-ai/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── documents.py    # Upload, status, delete
│   │   │   ├── query.py        # RAG query endpoint
│   │   │   └── risk.py         # Risk analysis + comparison
│   │   └── deps.py             # DB session dependency
│   ├── core/
│   │   ├── config.py           # Settings via pydantic-settings
│   │   └── celery_app.py       # Celery configuration
│   ├── models/
│   │   ├── db.py               # SQLAlchemy models
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── services/
│   │   ├── parser.py           # Clause-aware PDF parser ⭐
│   │   ├── vector_store.py     # Qdrant operations + embedding
│   │   ├── rag_engine.py       # Core RAG pipeline ⭐
│   │   └── risk_analyzer.py    # Celery risk analysis task
│   └── main.py                 # FastAPI app + lifespan
├── scripts/
│   └── evaluate.py             # RAGAS evaluation ⭐
├── tests/
│   └── test_core.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## License

MIT
