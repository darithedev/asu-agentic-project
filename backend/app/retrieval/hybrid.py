"""Hybrid RAG/CAG implementation for Booking/Payments agent."""

import logging
from typing import Dict, List, Optional

from app.retrieval.cag import CAGRetriever
from app.retrieval.rag import RAGRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid RAG/CAG retriever for Booking/Payments agent.
    
    Strategy:
    1. Initial RAG query to retrieve dynamic pricing/booking information
    2. Cache static policy documents for the session (CAG)
    3. Combine both dynamic and cached information in responses
    """

    def __init__(
        self,
        rag_retriever: Optional[RAGRetriever] = None,
        cag_retriever: Optional[CAGRetriever] = None,
    ):
        """
        Initialize the hybrid retriever.

        Args:
            rag_retriever: RAG retriever instance (will create if None)
            cag_retriever: CAG retriever instance (will create if None)
        """
        self.rag_retriever = rag_retriever or RAGRetriever(
            collection_name=None  # Will use default from config
        )
        self.cag_retriever = cag_retriever or CAGRetriever()
        
        # Cache for static policy documents (loaded once per session)
        self.static_policy_cache: List[str] = []
        self.cache_initialized = False
        
        logger.info("Initialized Hybrid RAG/CAG retriever")

    def initialize_cache(self, agent_type: str = "booking_payments") -> None:
        """
        Initialize the static policy cache (CAG strategy).

        Args:
            agent_type: Type of agent
        """
        if not self.cache_initialized:
            # Cache policy documents that are relevant for bookings/payments
            # These are static and don't change frequently
            self.cag_retriever.cache_documents(agent_type="policy")
            policy_docs = self.cag_retriever.get_cached_documents("policy")
            
            # Filter for relevant policy documents (payment, cancellation, refund policies)
            relevant_policies = []
            policy_keywords = ["payment", "cancellation", "refund", "booking", "terms"]
            
            for doc in policy_docs:
                doc_lower = doc.lower()
                if any(keyword in doc_lower for keyword in policy_keywords):
                    relevant_policies.append(doc)
            
            self.static_policy_cache = relevant_policies
            self.cache_initialized = True
            logger.info(f"Cached {len(relevant_policies)} relevant policy documents")

    def retrieve(
        self,
        query: str,
        agent_type: str = "booking_payments",
        top_k: int = 5,
        include_static: bool = True,
    ) -> Dict[str, List[dict]]:
        """
        Retrieve both dynamic (RAG) and static (CAG) information.

        Args:
            query: User query string
            agent_type: Type of agent
            top_k: Number of dynamic documents to retrieve
            include_static: Whether to include cached static policies

        Returns:
            Dictionary with 'dynamic' and 'static' keys containing retrieved documents
        """
        # Initialize cache if not done
        if not self.cache_initialized:
            self.initialize_cache(agent_type)

        results = {
            "dynamic": [],
            "static": [],
        }

        # 1. RAG retrieval for dynamic pricing/booking information
        try:
            dynamic_docs = self.rag_retriever.retrieve(
                query=query,
                agent_type=agent_type,
                top_k=top_k,
            )
            results["dynamic"] = dynamic_docs
            logger.info(f"Retrieved {len(dynamic_docs)} dynamic documents")
        except Exception as e:
            logger.error(f"Error in RAG retrieval: {e}")

        # 2. Get cached static policies if requested
        if include_static:
            # Search cached policies for relevant information
            matching_policies = self.cag_retriever.search_cached(
                query=query,
                agent_type="policy",
            )
            
            # Format as documents with metadata
            static_docs = []
            for policy_doc in matching_policies[:3]:  # Limit to top 3 most relevant
                static_docs.append({
                    "content": policy_doc,
                    "metadata": {
                        "agent_type": "policy",
                        "document_type": "static_policy",
                        "source": "cached",
                    },
                })
            
            results["static"] = static_docs
            logger.info(f"Retrieved {len(static_docs)} static policy documents")

        return results

    def get_static_policies(self) -> List[str]:
        """
        Get all cached static policy documents.

        Returns:
            List of static policy document contents
        """
        if not self.cache_initialized:
            self.initialize_cache()
        
        return self.static_policy_cache.copy()

    def clear_cache(self) -> None:
        """Clear the static policy cache."""
        self.static_policy_cache.clear()
        self.cache_initialized = False
        self.cag_retriever.clear_cache()
        logger.info("Cleared hybrid retriever cache")

