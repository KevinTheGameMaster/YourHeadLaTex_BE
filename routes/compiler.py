from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from dotenv import load_dotenv
import httpx
import os

from schemas import CompileRequest

load_dotenv()

router = APIRouter(prefix="/compile", tags=["compiler"])

LATEX_API_PRIMARY  = os.getenv("LATEX_API_PRIMARY")


async def compile_via_ytotech(content: str, engine: str) -> bytes:
    payload = {
        "compiler": engine,
        "resources": [
            {
                "main": True,
                "content": content,
            }
        ]
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        res = await client.post(
            LATEX_API_PRIMARY,
            json=payload,
        )

        # Ganti == 200 dengan in (200, 201)
        if res.status_code in (200, 201) and "application/pdf" in res.headers.get("content-type", ""):
            return res.content

        try:
            detail = res.json()
            log = detail.get("logs", res.text[:1000])
        except Exception:
            log = res.text[:1000]

        raise ValueError(f"Status {res.status_code}:\n{log}")


@router.post("")
async def compile_latex(req: CompileRequest):
    errors = []

    try:
        pdf_bytes = await compile_via_ytotech(req.content, req.engine)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        errors.append(f"Primary ({LATEX_API_PRIMARY}): {e}")

    raise HTTPException(503, {
        "error": "Semua compiler API gagal",
        "log": "\n".join(errors),
    })