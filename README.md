# LegalDoc AI

AI-powered legal document intelligence. Upload any contract or legal PDF and ask questions, detect risky clauses, and compare contract versions — all running locally with no API costs.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| API | FastAPI + Uvicorn |
| LLM | Ollama (llama3.2:3b) — runs locally |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | Qdrant |
| Background Jobs | Celery + Redis |
| Database | PostgreSQL + SQLAlchemy |
| Containerization | Docker + Docker Compose |

## Quick Start

```bash
git clone https://github.com/mohit-200/Lex-ai.git
cd Lex-ai
cp .env .env.local   # add your Google OAuth credentials if needed
docker compose up -d --build
```

Pull the LLM model (first time only):
```bash
docker exec -it lex-ai-ollama-1 ollama pull llama3.2:3b
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |

## Features

- Natural language Q&A with clause-level citations
- Automated risk detection across 10 risk categories
- Contract version comparison with plain-English diffs
- Confidence scoring — tells you when it doesn't know
- JWT auth + Google OAuth sign-in
- Password reset flow

## License

MIT
