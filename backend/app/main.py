from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import query, health
from app.db.vector_store import init_db

app = FastAPI(title="DocuMind API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://documind.vercel.app",
        "https://documind-samnit007.vercel.app",
    ],
    allow_origin_regex=r"https://documind.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


app.include_router(health.router, prefix="/api")
app.include_router(query.router, prefix="/api")
