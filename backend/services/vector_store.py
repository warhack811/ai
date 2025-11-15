"""
services/vector_store.py - FAS 2 VERSION
------------------------
✅ ChromaDB persistent storage
✅ Sentence-transformers embeddings (Multilingual)
✅ Smart chunking with overlap
✅ Semantic search
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import hashlib
import time

logger = logging.getLogger(__name__)


class VectorStore:
    """
    ChromaDB wrapper for document embeddings
    
    Features:
    - Persistent storage
    - Multilingual support (TR + EN)
    - Smart chunking
    - Semantic search
    """
    
    def __init__(self, persist_directory: str = "./data/chromadb"):
        """
        Initialize ChromaDB with persistent storage
        
        Args:
            persist_directory: Dizin yolu
        """
        # Dizini oluştur
        persist_path = Path(persist_directory)
        persist_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at {persist_directory}")
        
        # ChromaDB client (persistent)
        self.client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Embedding model (Multilingual - Türkçe + İngilizce)
        logger.info("Loading sentence-transformers model...")
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
            device='cpu'  # GPU varsa 'cuda' yapabilirsiniz
        )
        logger.info("✓ Embedding model loaded")
        
        # Collection (documents için)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
        
        logger.info(f"✓ Collection ready: {self.collection.count()} documents")
    
    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> Dict:
        """
        Doküman ekle (smart chunking ile)
        
        Args:
            doc_id: Unique document ID
            text: Doküman içeriği
            metadata: Metadata (filename, type, etc.)
            chunk_size: Her chunk'ın max kelime sayısı
            chunk_overlap: Chunk'lar arası overlap (kelime)
        
        Returns:
            {"chunks_added": int, "doc_id": str}
        """
        logger.info(f"Adding document: {doc_id} ({len(text)} chars)")
        
        # Smart chunking
        chunks = self._smart_chunk(
            text=text,
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )
        
        logger.info(f"Document split into {len(chunks)} chunks")
        
        # Her chunk için embedding oluştur ve ekle
        chunk_ids = []
        chunk_texts = []
        chunk_embeddings = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Unique chunk ID
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Embedding hesapla
            embedding = self.embedding_model.encode(
                chunk,
                convert_to_numpy=True,
                show_progress_bar=False
            ).tolist()
            
            # Metadata
            chunk_meta = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_id": doc_id,
            }
            
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk)
            chunk_embeddings.append(embedding)
            chunk_metadatas.append(chunk_meta)
        
        # ChromaDB'ye batch ekle
        self.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            embeddings=chunk_embeddings,
            metadatas=chunk_metadatas,
        )
        
        logger.info(f"✓ Added {len(chunks)} chunks to ChromaDB")
        
        return {
            "chunks_added": len(chunks),
            "doc_id": doc_id,
            "status": "success"
        }
    
    def _smart_chunk(
        self,
        text: str,
        chunk_size: int = 512,
        overlap: int = 50,
    ) -> List[str]:
        """
        Akıllı chunking with sentence awareness
        
        Args:
            text: Metin
            chunk_size: Max kelime sayısı
            overlap: Overlap kelime sayısı
        
        Returns:
            List of chunks
        """
        # Sentence tokenization (basit versiyon)
        # Daha gelişmiş için nltk.sent_tokenize kullanabilirsiniz
        import re
        
        # Cümlelere ayır (. ! ? ile)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            words = sentence.split()
            word_count = len(words)
            
            # Chunk limit aşılıyor mu?
            if current_word_count + word_count > chunk_size and current_chunk:
                # Mevcut chunk'ı kaydet
                chunks.append(' '.join(current_chunk))
                
                # Overlap için son N kelimeyi tut
                if overlap > 0 and len(current_chunk) > 0:
                    # Son cümleleri tut (overlap kadar kelime)
                    overlap_text = ' '.join(current_chunk)
                    overlap_words = overlap_text.split()[-overlap:]
                    current_chunk = overlap_words
                    current_word_count = len(overlap_words)
                else:
                    current_chunk = []
                    current_word_count = 0
            
            # Cümleyi ekle
            current_chunk.extend(words)
            current_word_count += word_count
        
        # Son chunk'ı ekle
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Semantic search
        
        Args:
            query: Arama sorgusu
            top_k: En iyi K sonuç
            filter_metadata: Metadata filtresi (opsiyonel)
        
        Returns:
            List of results with score
        """
        # Query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True,
            show_progress_bar=False
        ).tolist()
        
        # ChromaDB search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,  # Metadata filter
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            # Distance -> Similarity (cosine)
            similarity = 1.0 - dist
            
            formatted_results.append({
                "text": doc,
                "metadata": meta,
                "score": similarity,
            })
        
        return formatted_results
    
    def delete_document(self, doc_id: str) -> Dict:
        """
        Dokümanı sil (tüm chunk'larıyla birlikte)
        
        Args:
            doc_id: Document ID
        
        Returns:
            {"deleted_chunks": int, "status": str}
        """
        # Doc_id ile başlayan tüm chunk'ları bul
        all_ids = self.collection.get()['ids']
        doc_chunk_ids = [id for id in all_ids if id.startswith(f"{doc_id}_chunk_")]
        
        if not doc_chunk_ids:
            return {"deleted_chunks": 0, "status": "not_found"}
        
        # Sil
        self.collection.delete(ids=doc_chunk_ids)
        
        logger.info(f"✓ Deleted {len(doc_chunk_ids)} chunks for doc {doc_id}")
        
        return {
            "deleted_chunks": len(doc_chunk_ids),
            "status": "success"
        }
    
    def list_documents(self) -> List[Dict]:
        """
        Tüm dokümanları listele (unique doc_id'ler)
        
        Returns:
            List of documents with metadata
        """
        # Tüm metadata'yı al
        all_data = self.collection.get(include=["metadatas"])
        
        # Unique doc_id'leri bul
        doc_map = {}
        for meta in all_data['metadatas']:
            doc_id = meta.get('doc_id')
            if doc_id and doc_id not in doc_map:
                doc_map[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta.get('filename', 'Unknown'),
                    "type": meta.get('type', 'unknown'),
                    "added_at": meta.get('added_at', 'unknown'),
                    "total_chunks": meta.get('total_chunks', 0),
                }
        
        return list(doc_map.values())
    
    def get_stats(self) -> Dict:
        """
        Vector store istatistikleri
        
        Returns:
            Statistics dict
        """
        total_chunks = self.collection.count()
        documents = self.list_documents()
        
        return {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "avg_chunks_per_doc": total_chunks / len(documents) if documents else 0,
        }


# ---------------------------------------------------------------------------
# Global singleton instance
# ---------------------------------------------------------------------------

_vector_store_instance = None

def get_vector_store() -> VectorStore:
    """Get or create global VectorStore instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance