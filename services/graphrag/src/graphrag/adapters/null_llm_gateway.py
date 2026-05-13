"""Null LLM gateway — returns placeholder (used until 4-c/4-d adapters are available)."""
from ..ports.llm_gateway import LlmGateway


class NullLlmGateway(LlmGateway):
    async def generate_report(self, evidence_payload: dict, role: str, tenant_id: str) -> str:
        return "[LLM gateway not configured — evidence payload available in response]"
