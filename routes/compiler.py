from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import subprocess, tempfile, os, shutil, glob

from schemas import CompileRequest

router = APIRouter(prefix="/compile", tags=["compiler"])

# Folder untuk menyimpan .sty, .cls, .bst custom
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))


def find_engine(engine: str) -> str:
    found = shutil.which(engine)
    if found:
        return found
    username = os.getenv("USERNAME", "")
    candidates = [
        rf"C:\Users\{username}\AppData\Local\Programs\MiKTeX\miktex\bin\x64\{engine}.exe",
        rf"C:\Program Files\MiKTeX\miktex\bin\x64\{engine}.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@router.post("")
async def compile_latex(req: CompileRequest):
    engine_path = find_engine(req.engine)

    if not engine_path:
        raise HTTPException(500, {
            "error": f"{req.engine} not found",
            "log": "Pastikan MiKTeX sudah terinstall dan PATH sudah diset."
        })

    project_tmp = os.path.join(os.path.dirname(__file__), "..", "_tmp")
    os.makedirs(project_tmp, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=os.path.abspath(project_tmp)) as tmpdir:
        tex_path = os.path.join(tmpdir, "main.tex")
        pdf_path = os.path.join(tmpdir, "main.pdf")

        # Tulis file .tex
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(req.content)

        # Salin semua file assets (.sty, .cls, .bst, .png, dll) ke tmpdir
        if os.path.isdir(ASSETS_DIR):
            for filepath in glob.glob(os.path.join(ASSETS_DIR, "*")):
                shutil.copy2(filepath, tmpdir)

        try:
            result = subprocess.run(
                [
                    engine_path,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory", tmpdir,
                    tex_path,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(408, "Compile timeout (30s)")

        if not os.path.exists(pdf_path):
            raise HTTPException(422, {
                "error": "Compile failed",
                "log": result.stdout + "\n" + result.stderr,
            })

        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        return Response(content=pdf_bytes, media_type="application/pdf")