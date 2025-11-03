"""Policy & Compliance agent implementing Pure CAG strategy."""

import logging
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.retrieval.cag import CAGRetriever

logger = logging.getLogger(__name__)


class PolicyAgent:
    """
    Policy & Compliance agent using Pure CAG strategy.
    
    Loads static policy documents once per session and uses them
    for fast, consistent responses about policies and terms.
    """

    def __init__(self, cag_retriever: Optional[CAGRetriever] = None):
        """
        Initialize the Policy agent.

        Args:
            cag_retriever: CAG retriever instance (will create if None)
        """
        self.retriever = cag_retriever or CAGRetriever()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,  # Lower temperature for accurate, consistent policy responses
        )
        # Cache documents on initialization
        self.retriever.cache_documents("policy")
        logger.info("Initialized Policy agent (Pure CAG)")

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None,
        top_k: int = 5,
    ) -> str:
        """
        Generate a response using cached static documents (CAG strategy).

        Args:
            query: User's query string
            conversation_history: Optional conversation history
            top_k: Number of policy documents to retrieve (not used in CAG, but kept for API consistency)

        Returns:
            Generated response string
        """
        # Search cached policy documents
        matching_policies = self.retriever.search_cached(
            query=query,
            agent_type="policy",
        )

        # If no matches, use all cached documents
        if not matching_policies:
            matching_policies = self.retriever.get_cached_documents("policy")[:3]

        # Build context from matching policy documents
        context_parts = []
        for i, policy_doc in enumerate(matching_policies[:5], 1):  # Limit to top 5
            context_parts.append(f"[Policy Document {i}]\n{policy_doc}\n")

        context = "\n---\n".join(context_parts)

        # Build system prompt
        system_prompt = """You are a policy and compliance specialist for a travel agency.
Your role is to provide accurate information about:
- Cancellation policies and refund terms
- Terms of Service
- Travel insurance policies
- Baggage policies
- Other policy-related questions

Use the provided policy documents to answer questions accurately. Always be precise and reference
specific policy terms when relevant. If a policy document doesn't contain information about a
specific question, clearly state that.

Be professional, clear, and ensure you're providing accurate policy information."""

        # Build user prompt
        user_prompt = f"""Policy Documents:
{context}

User question: {query}

Provide a precise response based on the policy documents above. Quote specific policy terms when relevant."""

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

