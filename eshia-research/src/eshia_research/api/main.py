from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eshia_research.api.routes_books import router as books_router
from eshia_research.api.routes_search import router as search_router
from eshia_research.config import get_settings

settings = get_settings()
allowed_origins = [
    origin.strip()
    for origin in settings.api_allowed_origins.split(",")
    if origin.strip()
]

app = FastAPI(
    title="eShia Research API",
    description="Local-first API over a mirrored subset of the eShia digital library.",
    version="0.1.0",
    docs_url="/docs" if settings.api_enable_docs else None,
    redoc_url="/redoc" if settings.api_enable_docs else None,
    openapi_url="/openapi.json" if settings.api_enable_docs else None,
)

# Local Next.js dev server (web/) — every route here is read-only, so this is
# deliberately narrow (one hardcoded origin, GET only) rather than wildcarded.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "PUT"] if settings.api_admin_token else ["GET"],
    allow_headers=["Content-Type", "X-Admin-Token"],
)

app.include_router(books_router)
app.include_router(search_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
