from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routes import documents, compiler, ws

import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

app = FastAPI(title="YourHeadLaTeX Editor API", root_path=BASE_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(documents.router)
app.include_router(compiler.router)
app.include_router(ws.router)

@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}