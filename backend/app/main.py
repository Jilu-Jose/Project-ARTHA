"""
ARTHA — FastAPI Application Factory
=====================================
Advisory for Regulatory and Tax-related Holistic Advisories

Production-grade legal intelligence platform using Vectorless RAG:
BM25 sparse retrieval + NVIDIA NIM Kimi K2.6 long-context LLM.

No LangChain. No vector databases. No embedding models.
This is a deliberate architectural choice.
"""

import os
import logging
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import HealthResponse, ErrorResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
def setup_logging():
    """Configure structured logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.ENVIRONMENT == "production":
        # JSON formatter for production
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info:
                    log_record["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_record)

        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
    else:
        # Human-readable for development
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    logging.root.handlers = [handler]
    logging.root.setLevel(log_level)


# ---------------------------------------------------------------------------
# Application Lifespan (startup/shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    - Startup: Load BM25 indexes, verify connections
    - Shutdown: Close connections
    """
    setup_logging()
    logger.info("=" * 60)
    logger.info("  ARTHA Starting Up")
    logger.info(f"  Environment: {settings.ENVIRONMENT}")
    logger.info(f"  LLM Model: {settings.NVIDIA_MODEL}")
    logger.info("=" * 60)

    # Load BM25 indexes into memory
    await _load_retriever(app)

    # Initialize SQLite database
    from app.db.database import init_db
    await init_db()

    # Initialize Redis connection
    from app.core.cache import get_redis
    await get_redis()

    yield

    # Shutdown
    logger.info("ARTHA shutting down...")
    from app.core.cache import close_redis
    await close_redis()


async def _load_retriever(app: FastAPI):
    """Load BM25 indexes from disk at startup."""
    from app.core.retriever import ARTHARetriever

    index_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        settings.BM25_INDEX_DIR,
    )

    try:
        if os.path.exists(os.path.join(index_dir, "index_meta.json")):
            retriever = ARTHARetriever.load(index_dir)
            app.state.retriever = retriever
            stats = retriever.get_stats()
            logger.info(
                f"BM25 indexes loaded: {stats['total_chunks']} chunks, "
                f"domains: {list(stats['domains'].keys())}"
            )
        else:
            logger.warning(
                f"No BM25 indexes found at {index_dir}. "
                f"Run 'python scripts/build_index.py' to build indexes."
            )
            app.state.retriever = None
    except Exception as e:
        logger.error(f"Failed to load BM25 indexes: {e}")
        app.state.retriever = None


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_TITLE,
        description=(
            "Legal intelligence for Indian startup founders. "
            "Vectorless RAG: BM25 + NVIDIA NIM Kimi K2.6."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Global exception handler ---
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_code": f"HTTP_{exc.status_code}"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred.",
                "error_code": "INTERNAL_ERROR",
            },
        )

    # --- Routes ---
    from app.api.routes.auth import router as auth_router
    from app.api.routes.query import router as query_router
    from app.api.routes.corpus import router as corpus_router
    from app.api.routes.conversations import router as conversations_router
    from app.api.routes.analytics import router as analytics_router

    app.include_router(auth_router, prefix="/api")
    app.include_router(query_router, prefix="/api")
    app.include_router(corpus_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")

    # --- Health check ---
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """
        Health check endpoint.
        Verifies database, Redis, LLM API, and retriever status.
        """
        from app.db.database import check_db_health
        from app.core.cache import check_redis_health

        db_ok = await check_db_health()
        redis_ok = await check_redis_health()

        retriever = getattr(app.state, "retriever", None)
        retriever_loaded = retriever is not None
        total_chunks = retriever.get_stats()["total_chunks"] if retriever else 0

        # LLM health check is expensive, skip in frequent health checks
        llm_ok = bool(settings.NVIDIA_API_KEY)

        overall = "healthy" if (db_ok and retriever_loaded) else "degraded"

        return HealthResponse(
            status=overall,
            database=db_ok,
            redis=redis_ok,
            llm=llm_ok,
            retriever_loaded=retriever_loaded,
            total_chunks=total_chunks,
            version=settings.APP_VERSION,
        )

    # --- Root redirect ---
    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "name": "ARTHA",
            "description": "Advisory for Regulatory and Tax-related Holistic Advisories",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


# Create the app instance
app = create_app()
