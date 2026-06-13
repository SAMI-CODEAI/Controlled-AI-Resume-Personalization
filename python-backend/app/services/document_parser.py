import os
import io
import logging
from typing import Optional
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from a PDF file byte stream."""
    try:
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return ""

def extract_text_from_docx(content: bytes) -> str:
    """Extract text from a DOCX file byte stream."""
    try:
        doc = Document(io.BytesIO(content))
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text).strip()
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {e}")
        return ""

def extract_text_from_txt(content: bytes) -> str:
    """Extract text from a TXT file byte stream."""
    try:
        return content.decode("utf-8").strip()
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1").strip()
        except Exception as e:
            logger.error(f"Failed to extract text from TXT: {e}")
            return ""

def parse_file(filename: str, content: bytes) -> str:
    """Parse a file based on its extension and return its text content."""
    extension = os.path.splitext(filename)[1].lower()
    
    if extension == ".pdf":
        return extract_text_from_pdf(content)
    elif extension == ".docx":
        return extract_text_from_docx(content)
    elif extension == ".txt":
        return extract_text_from_txt(content)
    else:
        logger.warning(f"Unsupported file extension: {extension}")
        return ""
