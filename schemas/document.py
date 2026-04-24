from pydantic import BaseModel
from datetime import datetime

DEFAULT_CONTENT = r"""\documentclass{article}
\begin{document}
Hello World!
\end{document}"""

class DocumentCreate(BaseModel):
    title: str
    content: str = DEFAULT_CONTENT

class DocumentUpdate(BaseModel):
    content: str

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class CompileRequest(BaseModel):
    content: str
    engine: str = "pdflatex"