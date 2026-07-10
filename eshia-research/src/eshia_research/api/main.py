from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eshia_research.api.routes_books import router as books_router
from eshia_research.api.routes_search import router as search_router

app = FastAPI(
    title="eShia Research API",
    description="Local-first API over a mirrored subset of the eShia digital library.",
    version="0.1.0",
)

# Local Next.js dev server (web/) — every route here is read-only, so this is
# deliberately narrow (one hardcoded origin, GET only) rather than wildcarded.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "PUT"],
    allow_headers=["*"],
)

app.include_router(books_router)
app.include_router(search_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
