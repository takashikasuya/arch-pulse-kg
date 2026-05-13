"""LLM gateway port — IF-AI-002 (CS-AI-LLM-LOCAL / CLOUD)."""
from abc import ABC, abstractmethod


class LlmGateway(ABC):
    @abstractmethod
    async def generate_report(
        self,
        evidence_payload: dict,
        role: str,
        tenant_id: str,
    ) -> str:
        """Generate a role-specific report from the evidence payload."""
