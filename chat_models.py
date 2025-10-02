from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    """Represents a single message in the conversation."""

    author: str
    content: str


@dataclass
class AgentResponse:
    """Represents the agent response with optional metadata."""

    message: ChatMessage
    metadata: dict = field(default_factory=dict)
