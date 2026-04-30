import logging
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.user_document import UserDocument, HAS_VECTOR
from app.config import settings
import openai

logger = logging.getLogger(__name__)

client = openai.Client(
    api_key=settings.OPENAI_API_KEY or "dummy-key",
    base_url=settings.LLM_BASE_URL
)

# Use Ollama embedding model locally, or real OpenAI model if remote
EMBEDDING_MODEL = "nomic-embed-text" if "localhost" in settings.LLM_BASE_URL or "127.0.0.1" in settings.LLM_BASE_URL else "text-embedding-3-small"


def generate_embedding(text_content: str) -> List[float]:
    """Generate embedding for a given text."""
    try:
        response = client.embeddings.create(
            input=[text_content],
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        # Return a zero vector matching default OpenAI size 1536
        return [0.0] * 1536


def chunk_text(text_content: str, chunk_size: int = 500) -> List[str]:
    """Simple text chunker: split by paragraphs then by length."""
    paragraphs = [p.strip() for p in text_content.split('\n') if p.strip()]
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = p
        else:
            current_chunk += " " + p if current_chunk else p
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def ingest_user_document(db: Session, user_id: str, raw_text: str) -> int:
    """Chunk text, generate embeddings, and store them in the DB. Returns number of chunks."""
    chunks = chunk_text(raw_text)
    docs = []
    for chunk in chunks:
        embedding = generate_embedding(chunk)
        doc = UserDocument(
            user_id=user_id,
            content=chunk,
            embedding=embedding if any(embedding) else None
        )
        db.add(doc)
        docs.append(doc)
    db.commit()
    return len(docs)


def retrieve_relevant_past_impacts(db: Session, user_id: str, query: str, top_k: int = 3) -> List[str]:
    """Search for relevant past impact metrics/accomplishments based on the query."""
    if not query.strip():
        return []
    
    # Fallback if vector search is not viable locally for SQLite
    if not HAS_VECTOR or db.bind.dialect.name != "postgresql":
        logger.warning("Vector search is not available. Using SQLite fallback semantics.")
        docs = db.query(UserDocument).filter(UserDocument.user_id == user_id).limit(top_k).all()
        return [doc.content for doc in docs]

    query_embedding = generate_embedding(query)
    
    if not any(query_embedding):
        return []
        
    try:
        # Semantic search using pgvector's L2 distance
        docs = db.query(UserDocument).filter(
            UserDocument.user_id == user_id
        ).order_by(
            UserDocument.embedding.l2_distance(query_embedding)
        ).limit(top_k).all()
        
        return [doc.content for doc in docs]
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        # Hard fallback to recent documents in case of missing extension
        docs = db.query(UserDocument).filter(UserDocument.user_id == user_id).limit(top_k).all()
        return [doc.content for doc in docs]
