"""Travel Support agent implementing Pure RAG strategy."""

import logging
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.retrieval.rag import RAGRetriever

logger = logging.getLogger(__name__)


class TravelSupportAgent:
    """
    Travel Support agent using Pure RAG strategy.
    
    Retrieves relevant information from the knowledge base for each query
    and generates responses using OpenAI.
    """

    def __init__(self, rag_retriever: Optional[RAGRetriever] = None):
        """
        Initialize the Travel Support agent.

        Args:
            rag_retriever: RAG retriever instance (will create if None)
        """
        self.retriever = rag_retriever or RAGRetriever()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.7,  # Higher temperature for more conversational responses
        )
        logger.info("Initialized Travel Support agent (Pure RAG)")

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[List[dict]] = None,
        top_k: int = 5,
    ) -> str:
        """
        Generate a response to a user query using RAG.

        Args:
            query: User's query string
            conversation_history: Optional conversation history
            top_k: Number of documents to retrieve

        Returns:
            Generated response string
        """
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(
            query=query,
            agent_type="travel_support",
            top_k=top_k,
        )

        # Build context from retrieved documents
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source_file", "unknown")
            context_parts.append(f"[Document {i} from {source}]\n{content}\n")

        context = "\n---\n".join(context_parts)

        # Build system prompt
        system_prompt = """You are a helpful travel support agent for a travel agency.
Your role is to provide accurate, friendly, and helpful information about travel destinations,
itineraries, travel tips, and general travel advice.

Use the provided context documents to answer questions accurately. If the context doesn't contain
enough information to fully answer the question, say so and provide what information you can.

IMPORTANT FORMATTING GUIDELINES:
- Keep responses concise and well-structured
- Use bullet points (-) or numbered lists (1., 2., 3.) for multiple items
- Use bold text (**text**) for emphasis on important terms like dates, prices, or key information
- Use section headings (### Heading) to organize content into clear sections
- Break long responses into clear sections with line breaks between sections
- When asking follow-up questions, format them as a simple numbered or bulleted list
- Keep paragraphs to 2-3 sentences maximum
- Ensure proper spacing: leave blank lines between major sections

Always be friendly, professional, and helpful. Provide practical, actionable advice."""

        # Build user prompt with context
        user_prompt = f"""Context from knowledge base:
{context}

User question: {query}

Provide a helpful, concise, and well-structured response based on the context above. 
If the context doesn't fully answer the question, acknowledge this and provide the best answer you can.
Format your response clearly with appropriate structure (bullets, sections, etc.) for easy reading."""

        try:
            messages = [SystemMessage(content=system_prompt)]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history[-4:]:  # Last 4 messages for context
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(HumanMessage(content=content))
                    # Note: We're not adding assistant messages for simplicity
            
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

