"""
Agent — thin re-export of HermesAgent.
Keeps all specialist/orchestrator imports unchanged.
"""
from backend.core.hermes_agent import HermesAgent as Agent, AgentContext, Message

__all__ = ["Agent", "AgentContext", "Message"]
