"""Pure RAG (Retrieval Augmented Generation) implementation for Travel Support agent."""

import logging
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Pure RAG retriever for dynamic retrieval from vector database.
    
    Used by Travel Support agent to retrieve relevant information
    from the knowledge base for each query.
    """

    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize the RAG retriever.

        Args:
            collection_name: Name of ChromaDB collection (defaults to config)
        """
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embeddings = OpenAIEmbeddings(model=settings.openai_embedding_model)
        
        # Initialize ChromaDB client
        db_path = settings.chroma_db_absolute_path
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except Exception as e:
            logger.error(f"Failed to load collection {self.collection_name}: {e}")
            raise

    def retrieve(
        self,
        query: str,
        agent_type: str = "travel_support",
        top_k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> List[dict]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: User query string
            agent_type: Type of agent (used for metadata filtering)
            top_k: Number of documents to retrieve
            filter_metadata: Additional metadata filters

        Returns:
            List of dictionaries with 'content' and 'metadata' keys
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Build metadata filter
            where_clause = {"agent_type": agent_type}
            if filter_metadata:
                where_clause.update(filter_metadata)
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None,
            )
            
            # Format results
            documents = []
            if results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    doc = {
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    }
                    # Add distance if available
                    if results.get("distances") and results["distances"][0]:
                        doc["distance"] = results["distances"][0][i]
                    
                    documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []

    def retrieve_with_scores(
        self,
        query: str,
        agent_type: str = "travel_support",
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> List[dict]:
        """
        Retrieve documents with similarity scores and apply threshold.

        Args:
            query: User query string
            agent_type: Type of agent
            top_k: Number of documents to retrieve
            score_threshold: Minimum similarity score (lower is better for distance)

        Returns:
            List of documents with scores above threshold
        """
        documents = self.retrieve(query, agent_type, top_k)
        
        # Filter by distance threshold (ChromaDB uses distance, lower is better)
        # Convert distance to similarity score if needed
        filtered_docs = []
        for doc in documents:
            distance = doc.get("distance", 1.0)
            # For cosine distance, similarity is approximately 1 - distance
            similarity = 1 - distance if distance <= 1.0 else 0
            if similarity >= score_threshold:
                doc["similarity"] = similarity
                filtered_docs.append(doc)
        
        return filtered_docs

