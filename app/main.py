from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.api.routes import documents, query, risk, auth
from app.core.config import settings
from app.models.db import Base
from app.api.deps import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="LegalDoc AI",
    description="""
## AI-powered legal document intelligence API

Upload any contract or legal PDF and:
- **Ask natural language questions** with clause-level citations
- **Detect risky clauses** automatically (liability, auto-renewal, IP assignment, etc.)
- **Compare contract versions** with plain-English explanations of what changed

Built with FastAPI · Qdrant · LangChain · GPT-4o · Celery
    """,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(risk.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LegalDoc AI"}
