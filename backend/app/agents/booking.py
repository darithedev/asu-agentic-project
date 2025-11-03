"""Booking/Payments agent implementing Hybrid RAG/CAG strategy."""

import logging
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.retrieval.hybrid import HybridRetriever

logger = logging.getLogger(__name__)


class BookingPaymentsAgent:
    """
    Booking/Payments agent using Hybrid RAG/CAG strategy.
    
    Strategy:
    1. Initial RAG query for dynamic pricing/booking information
    2. Uses cached static policies (CAG) for consistent policy information
    3. Combines both in responses
    """

    def __init__(self, hybrid_retriever: Optional[HybridRetriever] = None):
        """
        Initialize the Booking/Payments agent.

        Args:
            hybrid_retriever: Hybrid retriever instance (will create if None)
        """
        self.retriever = hybrid_retriever or HybridRetriever()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.5,  # Moderate temperature for accurate pricing info
        )
        # Initialize cache on startup
        self.retriever.initialize_cache("booking_payments")
        logger.info("Initialized Booking/Payments agent (Hybrid RAG/CAG)")

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None,
        top_k: int = 5,
    ) -> str:
        """
        Generate a response using Hybrid RAG/CAG strategy.

        Args:
            query: User's query string
            conversation_history: Optional conversation history
            top_k: Number of dynamic documents to retrieve

        Returns:
            Generated response string
        """
        # Retrieve both dynamic and static information
        retrieval_results = self.retriever.retrieve(
            query=query,
            agent_type="booking_payments",
            top_k=top_k,
            include_static=True,
        )

        dynamic_docs = retrieval_results.get("dynamic", [])
        static_docs = retrieval_results.get("static", [])

        # Build context from dynamic documents
        dynamic_context_parts = []
        for i, doc in enumerate(dynamic_docs, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source_file", "unknown")
            dynamic_context_parts.append(f"[Dynamic Info {i} from {source}]\n{content}\n")

        dynamic_context = "\n---\n".join(dynamic_context_parts)

        # Build context from static policy documents
        static_context_parts = []
        for i, doc in enumerate(static_docs, 1):
            content = doc.get("content", "")
            static_context_parts.append(f"[Policy Information {i}]\n{content}\n")

        static_context = "\n---\n".join(static_context_parts)

        # Build system prompt
        system_prompt = """You are a booking and payments specialist for a travel agency.
Your role is to help customers with:
- Package pricing and costs
- Payment methods and processes
- Booking information and invoices
- Pricing details for flights, hotels, and packages

Use the provided context documents (both dynamic pricing info and static policies) to answer
questions accurately. Always reference specific pricing when available, and note that prices
may vary based on dates, availability, and other factors.

Be professional, clear, and helpful. When discussing pricing, be specific about what's included."""

        # Build user prompt
        user_prompt_parts = []
        
        if dynamic_context:
            user_prompt_parts.append(f"Dynamic Pricing/Booking Information:\n{dynamic_context}")
        
        if static_context:
            user_prompt_parts.append(f"Policy Information (Static):\n{static_context}")
        
        if not dynamic_context and not static_context:
            user_prompt_parts.append("No specific information found in knowledge base.")
        
        user_prompt_parts.append(f"\nUser question: {query}")
        user_prompt_parts.append(
            "\nProvide a helpful response based on the context above. "
            "Combine dynamic pricing information with policy information as needed."
        )
        
        user_prompt = "\n\n".join(user_prompt_parts)

        try:
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-4:]:  # Last 4 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
            
            messages.append(HumanMessage(content=user_prompt))

            response = self.llm.invoke(messages)
            response_content = response.content.strip() if response.content else ""
            
            # Validate response is not empty
            if not response_content:
                logger.warning(f"Empty response from LLM for query: {query[:50]}...")
                return "I apologize, but I couldn't generate a response. Please try again or contact customer support."
            
            return response_content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while generating a response. Please try again or contact customer support."

