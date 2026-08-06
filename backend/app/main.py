"""RAPID-Learn FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import concepts, learners, questions
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.seed import initialise_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    initialise_database()
    yield


settings = get_settings()
app = FastAPI(title="RAPID-Learn API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(learners.router)
app.include_router(concepts.router)
app.include_router(questions.router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "rapid-learn"}
