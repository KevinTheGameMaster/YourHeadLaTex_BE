from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import Document
from schemas import DocumentCreate, DocumentUpdate, DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("", response_model=DocumentResponse)
def create_document(doc: DocumentCreate, db: Session = Depends(get_db)):
    new_doc = Document(
        id      = str(uuid.uuid4())[:8],
        title   = doc.title,
        content = doc.content,
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.put("/{doc_id}", response_model=DocumentResponse)
def update_document(doc_id: str, body: DocumentUpdate, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    doc.content = body.content
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
    return {"message": f"Document {doc_id} deleted"}