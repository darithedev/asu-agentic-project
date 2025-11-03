"""Orchestrator agent for routing queries to specialized worker agents."""

import json
import logging
from typing import Literal

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.models.state import AgentRoutingDecision

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """
    Orchestrator agent that routes user queries to appropriate specialized agents.
    
    Uses AWS Bedrock (Claude Haiku) for cost-effective routing decisions.
    """

    def __init__(self):
        """Initialize the orchestrator agent with AWS Bedrock."""
        try:
            self.llm = ChatBedrock(
                model_id=settings.bedrock_model_id,
                region_name=settings.aws_region,
                credentials_profile_name=None,  # Uses default AWS credentials
                model_kwargs={
                    "temperature": 0.3,  # Lower temperature for consistent routing
                    "max_tokens": 200,
                },
            )
            logger.info(f"Initialized orchestrator with Bedrock model: {settings.bedrock_model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise

    def route_query(self, query: str) -> AgentRoutingDecision:
        """
        Route a user query to the appropriate agent.

        Args:
            query: User's query string

        Returns:
            AgentRoutingDecision with agent_type, confidence, and reasoning
        """
        system_prompt = """You are a routing agent for a travel agency customer service system.
Your job is to analyze customer queries and route them to the most appropriate specialized agent.

Available agents:
1. travel_support - Handles questions about destinations, travel tips, itineraries, general travel advice
2. booking_payments - Handles questions about pricing, packages, payments, invoices, booking costs
3. policy - Handles questions about cancellation policies, refunds, terms of service, travel insurance, baggage policies

Analyze the query and respond with ONLY a JSON object in this exact format:
{
    "agent_type": "travel_support" | "booking_payments" | "policy",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}

Be precise and choose the most appropriate agent based on the query's primary concern."""

        human_prompt = f"Route this query: {query}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Extract JSON from response (handle cases where LLM adds extra text)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                routing_data = json.loads(json_str)
            else:
                # Fallback: try to parse the whole response
                routing_data = json.loads(response_text)

            # Validate and create routing decision
            agent_type = routing_data.get("agent_type", "travel_support")
            if agent_type not in ["travel_support", "booking_payments", "policy"]:
                logger.warning(f"Invalid agent_type '{agent_type}', defaulting to travel_support")
                agent_type = "travel_support"

            confidence = float(routing_data.get("confidence", 0.7))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1

            reasoning = routing_data.get("reasoning", "No reasoning provided")

            decision = AgentRoutingDecision(
                agent_type=agent_type,
                confidence=confidence,
                reasoning=reasoning,
            )

            logger.info(
                f"Routed query to {agent_type} (confidence: {confidence:.2f}): {reasoning}"
            )
            return decision

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse routing response as JSON: {e}")
            # Fallback: simple keyword-based routing
            return self._fallback_routing(query)
        except Exception as e:
            logger.error(f"Error in routing query: {e}")
            return self._fallback_routing(query)

    def _fallback_routing(self, query: str) -> AgentRoutingDecision:
        """
        Fallback routing using keyword matching when LLM routing fails.

        Args:
            query: User's query string

        Returns:
            AgentRoutingDecision
        """
        query_lower = query.lower()

        # Keyword patterns for each agent type
        booking_keywords = [
            "price", "cost", "payment", "invoice", "booking", "package",
            "how much", "pricing", "pay", "refund", "charge"
        ]
        policy_keywords = [
            "policy", "cancel", "cancellation", "terms", "insurance",
            "baggage", "refund policy", "tos", "terms of service"
        ]

        booking_score = sum(1 for kw in booking_keywords if kw in query_lower)
        policy_score = sum(1 for kw in policy_keywords if kw in query_lower)

        if booking_score > policy_score and booking_score > 0:
            agent_type: Literal["travel_support", "booking_payments", "policy"] = "booking_payments"
            confidence = min(0.8, 0.5 + booking_score * 0.1)
            reasoning = "Matched booking/payment keywords"
        elif policy_score > 0:
            agent_type = "policy"
            confidence = min(0.8, 0.5 + policy_score * 0.1)
            reasoning = "Matched policy keywords"
        else:
            agent_type = "travel_support"
            confidence = 0.6
            reasoning = "Default fallback to travel support"

        return AgentRoutingDecision(
            agent_type=agent_type,
            confidence=confidence,
            reasoning=reasoning,
        )

