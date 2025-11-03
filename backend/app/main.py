"""FastAPI application entry point for Travel Agency Customer Service AI."""

import logging
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.chains.graph import create_agent_graph
from app.config import logger, settings
from app.models.schemas import ChatRequest, ChatResponse, Message, MessageRole

# Initialize FastAPI app
app = FastAPI(
    title="Travel Agency Customer Service AI",
    description="Multi-agent customer service system for travel agency",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LangGraph workflow (create once, reuse)
agent_graph = None


def get_agent_graph():
    """Get or create the agent graph instance."""
    global agent_graph
    if agent_graph is None:
        agent_graph = create_agent_graph()
    return agent_graph


# In-memory session storage (in production, use Redis or database)
sessions: dict[str, dict] = {}


def get_or_create_session(session_id: str | None) -> str:
    """
    Get existing session ID or create a new one.

    Args:
        session_id: Optional existing session ID

    Returns:
        Session ID string
    """
    if session_id and session_id in sessions:
        return session_id
    
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = {"messages": []}
    return new_session_id


def format_state_for_graph(messages: list[Message], query: str, session_id: str) -> dict:
    """
    Format state dictionary for LangGraph workflow.

    Args:
        messages: List of conversation messages
        query: Current user query
        session_id: Session ID

    Returns:
        Dictionary formatted for LangGraph GraphState
    """
    return {
        "messages": messages,
        "current_query": query,
        "routing_decision": None,
        "retrieved_context": None,
        "cached_data": None,
        "session_id": session_id,
        "current_agent": None,
        "response": None,
    }


async def stream_response(
    query: str, session_id: str, conversation_history: list[Message] | None
) -> AsyncGenerator[str, None]:
    """
    Stream response from agent workflow.

    Args:
        query: User query
        session_id: Session ID
        conversation_history: Optional conversation history

    Yields:
        Response chunks as strings
    """
    try:
        # Get or create session
        session_id = get_or_create_session(session_id)
        
        # Prepare messages
        if conversation_history is None:
            conversation_history = sessions[session_id].get("messages", [])
        
        # Add user message to conversation
        user_message = Message(role=MessageRole.USER, content=query)
        messages = conversation_history + [user_message]
        
        # Format state for graph
        initial_state = format_state_for_graph(messages, query, session_id)
        
        # Get agent graph
        graph = get_agent_graph()
        
        # Run workflow (streaming would require custom implementation)
        # For now, we'll run synchronously and stream the result
        result = graph.invoke(initial_state)
        
        # Get response from state
        response_text = result.get("response")
        
        # Debug logging
        logger.info(f"Response from graph: {response_text[:100] if response_text else 'None'}...")
        
        # Handle empty or None response
        if not response_text or not response_text.strip():
            logger.warning(f"Empty response from graph for query: {query[:50]}...")
            response_text = "I apologize, but I couldn't generate a response. Please try again."
        
        # Stream response token by token in SSE format
        # Frontend expects Server-Sent Events format with "data: " prefix
        # Frontend accumulates chunks directly, so we need to include spaces
        tokens = response_text.split()
        
        logger.info(f"Streaming {len(tokens)} tokens in SSE format")
        
        # Handle case where response might be empty after splitting
        if not tokens:
            error_message = "I apologize, but I couldn't generate a response. Please try again."
            yield f"data: {error_message}\n\n"
        else:
            # Send each token as an SSE event with proper spacing
            # Frontend accumulates chunks directly, so spaces must be included
            for i, token in enumerate(tokens):
                if i == 0:
                    # First token: no leading space
                    yield f"data: {token}\n\n"
                else:
                    # Subsequent tokens: include leading space for proper word separation
                    yield f"data:  {token}\n\n"  # Note: space after colon for spacing
            
            # Small delay for streaming effect (remove in production for faster response)
            # await asyncio.sleep(0.01)
        
        # Update session with assistant response
        assistant_message = Message(role=MessageRole.ASSISTANT, content=response_text)
        messages.append(assistant_message)
        sessions[session_id]["messages"] = messages
        
    except Exception as e:
        logger.error(f"Error in stream_response: {e}")
        error_message = f"Error: {str(e)}"
        yield f"data: {error_message}\n\n"


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "healthy",
        "service": "Travel Agency Customer Service AI",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Non-streaming chat endpoint.

    Args:
        request: Chat request with message and optional session_id

    Returns:
        Chat response with message and session_id
    """
    try:
        # Get or create session
        session_id = get_or_create_session(request.session_id)
        
        # Prepare messages
        conversation_history = request.conversation_history
        if conversation_history is None:
            conversation_history = sessions[session_id].get("messages", [])
        
        # Add user message
        user_message = Message(role=MessageRole.USER, content=request.message)
        messages = conversation_history + [user_message]
        
        # Format state for graph
        initial_state = format_state_for_graph(messages, request.message, session_id)
        
        # Get agent graph and run workflow
        graph = get_agent_graph()
        result = graph.invoke(initial_state)
        
        # Get response
        response_text = result.get("response")
        
        # Handle empty or None response
        if not response_text or not response_text.strip():
            logger.warning(f"Empty response from graph for query: {request.message[:50]}...")
            response_text = "I apologize, but I couldn't generate a response. Please try again."
        
        # Get agent type that handled the request
        agent_type = result.get("current_agent")
        
        # Update session
        assistant_message = Message(role=MessageRole.ASSISTANT, content=response_text)
        messages.append(assistant_message)
        sessions[session_id]["messages"] = messages
        
        return ChatResponse(
            message=response_text,
            session_id=session_id,
            agent_type=agent_type,
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).

    Args:
        request: Chat request with message and optional session_id

    Returns:
        StreamingResponse with SSE format
    """
    try:
        return StreamingResponse(
            stream_response(
                query=request.message,
                session_id=request.session_id or "",
                conversation_history=request.conversation_history,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Error in streaming chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Get session information and conversation history.

    Args:
        session_id: Session ID

    Returns:
        Session data including messages
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": sessions[session_id]["messages"],
        "message_count": len(sessions[session_id]["messages"]),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )

