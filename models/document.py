from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from base import Base  # <-- ganti ini

class Document(Base):
    __tablename__ = "documents"

    id         = Column(String(8),   primary_key=True, index=True)
    title      = Column(String(255), nullable=False)
    content    = Column(Text,        default="")
    created_at = Column(DateTime,    server_default=func.now())
    updated_at = Column(DateTime,    server_default=func.now(), onupdate=func.now())