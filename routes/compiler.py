from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
import httpx
import os

from schemas import CompileRequest

load_dotenv()

router = APIRouter(prefix="/compile", tags=["compiler"])

LATEX_API_PRIMARY  = os.getenv("LATEX_API_PRIMARY", "https://latexonline.cc/compile")
LATEX_API_FALLBACK = os.getenv("LATEX_API_FALLBACK", "https://texlive.net/run")


async def compile_via_latexonline(content: str, engine: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            LATEX_API_PRIMARY,
            params={"command": engine},
            content=content.encode("utf-8"),
            headers={"Content-Type": "application/x-tex"},
        )
        if res.status_code != 200 or "application/pdf" not in res.headers.get("content-type", ""):
            raise ValueError(f"Status {res.status_code}: {res.text[:300]}")
        return res.content


async def compile_via_texlive(content: str, engine: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            LATEX_API_FALLBACK,
            data={
                "filecontents[]": content,
                "filename[]": "main.tex",
                "engine": engine,
                "return": "pdf",
            },
        )
        if res.status_code != 200 or "application/pdf" not in res.headers.get("content-type", ""):
            raise ValueError(f"Status {res.status_code}: {res.text[:300]}")
        return res.content


@router.post("")
async def compile_latex(req: CompileRequest):
    errors = []

    try:
        pdf_bytes = await compile_via_latexonline(req.content, req.engine)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        errors.append(f"Primary ({LATEX_API_PRIMARY}): {e}")

    try:
        pdf_bytes = await compile_via_texlive(req.content, req.engine)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        errors.append(f"Fallback ({LATEX_API_FALLBACK}): {e}")

    raise HTTPException(503, {
        "error": "Semua compiler API gagal",
        "log": "\n".join(errors),
    })