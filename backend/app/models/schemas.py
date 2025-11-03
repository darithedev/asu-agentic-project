"""Pydantic schemas for API requests and responses."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in the conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in the conversation."""

    role: MessageRole = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message")
    timestamp: Optional[str] = Field(None, description="Optional timestamp for the message")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What are your cancellation policies?",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    message: str = Field(..., description="The user's message", min_length=1)
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID to maintain conversation context across requests",
    )
    conversation_history: Optional[List[Message]] = Field(
        None,
        description="Optional conversation history. If not provided, will be retrieved from session.",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "message": "What are your cancellation policies?",
                "session_id": "session_123",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Hello",
                        "timestamp": "2024-01-15T10:30:00Z",
                    },
                    {
                        "role": "assistant",
                        "content": "Hello! How can I help you today?",
                        "timestamp": "2024-01-15T10:30:05Z",
                    },
                ],
            }
        }


class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""

    message: str = Field(..., description="The assistant's response message")
    session_id: str = Field(..., description="The session ID for this conversation")
    agent_type: Optional[str] = Field(
        None,
        description="The type of agent that handled this request (travel_support, booking_payments, policy)",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "message": "Our cancellation policy allows full refunds up to 48 hours before departure...",
                "session_id": "session_123",
                "agent_type": "policy",
            }
        }

