"""LangGraph workflow definition for the multi-agent system."""

import logging
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.agents.booking import BookingPaymentsAgent
from app.agents.orchestrator import OrchestratorAgent
from app.agents.policy import PolicyAgent
from app.agents.travel_support import TravelSupportAgent
from app.models.schemas import Message, MessageRole

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """
    LangGraph state as TypedDict for compatibility.
    
    This wraps the Pydantic AgentGraphState model for use with LangGraph.
    """
    messages: list
    current_query: str | None
    routing_decision: dict | None
    retrieved_context: dict | None
    cached_data: dict | None
    session_id: str | None
    current_agent: str | None
    response: str | None


def create_agent_graph():
    """
    Create and compile the LangGraph workflow for the multi-agent system.

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize agents
    orchestrator = OrchestratorAgent()
    travel_support_agent = TravelSupportAgent()
    booking_agent = BookingPaymentsAgent()
    policy_agent = PolicyAgent()

    # Create graph
    workflow = StateGraph(GraphState)

    # Define nodes

    def entry_node(state: GraphState) -> GraphState:
        """
        Entry node: Extract query from state and prepare for routing.

        Args:
            state: Current graph state

        Returns:
            Updated state with current_query set
        """
        # Get the latest user message
        messages = state.get("messages", [])
        user_messages = [
            msg for msg in messages 
            if isinstance(msg, Message) and msg.role == MessageRole.USER
            or isinstance(msg, dict) and msg.get("role") == "user"
        ]
        
        if user_messages:
            last_msg = user_messages[-1]
            if isinstance(last_msg, Message):
                current_query = last_msg.content
            else:
                current_query = last_msg.get("content", "")
            state["current_query"] = current_query
            logger.info(f"Entry node: Processing query: {current_query[:50]}...")
        else:
            logger.warning("Entry node: No user message found in state")
            state["current_query"] = ""

        return state

    def orchestrator_node(state: GraphState) -> GraphState:
        """
        Orchestrator node: Route query to appropriate agent.

        Args:
            state: Current graph state

        Returns:
            Updated state with routing decision
        """
        query = state.get("current_query")
        if not query:
            logger.error("Orchestrator: No query found in state")
            return state

        try:
            routing_decision = orchestrator.route_query(query)
            # Convert Pydantic model to dict for state
            state["routing_decision"] = {
                "agent_type": routing_decision.agent_type,
                "confidence": routing_decision.confidence,
                "reasoning": routing_decision.reasoning,
            }
            state["current_agent"] = routing_decision.agent_type
            logger.info(
                f"Orchestrator: Routed to {routing_decision.agent_type} "
                f"(confidence: {routing_decision.confidence:.2f})"
            )
        except Exception as e:
            logger.error(f"Orchestrator error: {e}")
            # Fallback to travel_support
            state["routing_decision"] = {
                "agent_type": "travel_support",
                "confidence": 0.5,
                "reasoning": "Fallback due to orchestrator error",
            }
            state["current_agent"] = "travel_support"

        return state

    def route_agent(state: GraphState) -> Literal["travel_support", "booking_payments", "policy"]:
        """
        Conditional routing function based on orchestrator's decision.

        Args:
            state: Current graph state

        Returns:
            Next node name based on routing decision
        """
        routing_decision = state.get("routing_decision")
        if not routing_decision:
            logger.warning("Route agent: No routing decision, defaulting to travel_support")
            return "travel_support"

        agent_type = routing_decision.get("agent_type", "travel_support")
        logger.info(f"Routing to agent: {agent_type}")
        return agent_type

    def travel_support_node(state: GraphState) -> GraphState:
        """
        Travel Support agent node: Process query using Pure RAG.

        Args:
            state: Current graph state

        Returns:
            Updated state with response
        """
        query = state.get("current_query")
        if not query:
            logger.error("Travel Support: No query found in state")
            state["response"] = "I apologize, but I couldn't process your query."
            return state

        try:
            # Convert messages to format expected by agent
            messages = state.get("messages", [])
            conversation_history = []
            for msg in messages:
                if isinstance(msg, Message):
                    conversation_history.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
                elif isinstance(msg, dict):
                    conversation_history.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })

            response = travel_support_agent.generate_response(
                query=query,
                conversation_history=conversation_history,
            )
            state["response"] = response
            logger.info("Travel Support: Response generated successfully")

            # Add response to messages
            messages = state.get("messages", [])
            messages.append(Message(role=MessageRole.ASSISTANT, content=response))
            state["messages"] = messages

        except Exception as e:
            logger.error(f"Travel Support error: {e}")
            state["response"] = (
                "I apologize, but I encountered an error while processing "
                "your travel support question. Please try again."
            )

        return state

    def booking_payments_node(state: GraphState) -> GraphState:
        """
        Booking/Payments agent node: Process query using Hybrid RAG/CAG.

        Args:
            state: Current graph state

        Returns:
            Updated state with response
        """
        query = state.get("current_query")
        if not query:
            logger.error("Booking/Payments: No query found in state")
            state["response"] = "I apologize, but I couldn't process your query."
            return state

        try:
            # Convert messages to format expected by agent
            messages = state.get("messages", [])
            conversation_history = []
            for msg in messages:
                if isinstance(msg, Message):
                    conversation_history.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
                elif isinstance(msg, dict):
                    conversation_history.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })

            response = booking_agent.generate_response(
                query=query,
                conversation_history=conversation_history,
            )
            state["response"] = response
            logger.info("Booking/Payments: Response generated successfully")

            # Add response to messages
            messages = state.get("messages", [])
            messages.append(Message(role=MessageRole.ASSISTANT, content=response))
            state["messages"] = messages

        except Exception as e:
            logger.error(f"Booking/Payments error: {e}")
            state["response"] = (
                "I apologize, but I encountered an error while processing "
                "your booking/payment question. Please try again."
            )

        return state

    def policy_node(state: GraphState) -> GraphState:
        """
        Policy agent node: Process query using Pure CAG.

        Args:
            state: Current graph state

        Returns:
            Updated state with response
        """
        query = state.get("current_query")
        if not query:
            logger.error("Policy: No query found in state")
            state["response"] = "I apologize, but I couldn't process your query."
            return state

        try:
            # Convert messages to format expected by agent
            messages = state.get("messages", [])
            conversation_history = []
            for msg in messages:
                if isinstance(msg, Message):
                    conversation_history.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
                elif isinstance(msg, dict):
                    conversation_history.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })

            response = policy_agent.generate_response(
                query=query,
                conversation_history=conversation_history,
            )
            state["response"] = response
            logger.info("Policy: Response generated successfully")

            # Add response to messages
            messages = state.get("messages", [])
            messages.append(Message(role=MessageRole.ASSISTANT, content=response))
            state["messages"] = messages

        except Exception as e:
            logger.error(f"Policy error: {e}")
            state["response"] = (
                "I apologize, but I encountered an error while processing "
                "your policy question. Please try again."
            )

        return state

    # Add nodes to graph
    workflow.add_node("entry", entry_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("travel_support", travel_support_node)
    workflow.add_node("booking_payments", booking_payments_node)
    workflow.add_node("policy", policy_node)

    # Define edges
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "orchestrator")
    workflow.add_conditional_edges(
        "orchestrator",
        route_agent,
        {
            "travel_support": "travel_support",
            "booking_payments": "booking_payments",
            "policy": "policy",
        },
    )
    workflow.add_edge("travel_support", END)
    workflow.add_edge("booking_payments", END)
    workflow.add_edge("policy", END)

    # Compile graph
    app = workflow.compile()

    logger.info("LangGraph workflow created and compiled successfully")
    return app

