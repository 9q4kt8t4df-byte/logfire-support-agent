# orchestrator/orchestrator.py
from __future__ import annotations
import json
from typing import Optional
from pydantic import ValidationError
from api.models import ChatResponse, MessageRecord, SmokeAlert
from orchestrator.conversation import ConversationStore
from agents.supervisor import SupervisorAgent


class AgentOrchestrator:
    def __init__(self, supervisor: SupervisorAgent, db_url: str = "sqlite:///conversations.db") -> None:
        self.supervisor = supervisor
        self.store = ConversationStore(db_url=db_url)

    async def chat(
        self,
        message: str,
        case_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ChatResponse:
        if conversation_id:
            conv = self.store.get_conversation(conversation_id)
            if conv is None:
                raise ValueError(f"Conversation not found: {conversation_id}")
        else:
            conv = self.store.create_conversation()

        full_message = f"[Salesforce case_id: {case_id}]\n\n{message}" if case_id else message
        self.store.add_message(conv.id, role="user", content=full_message)

        history = self._build_history(conv.id)
        response_text = await self.supervisor.run(history)
        tools_used = list(self.supervisor.tools_used)

        self.store.add_message(conv.id, role="assistant", content=response_text)

        smoke_alert = self._extract_smoke_alert(response_text)

        return ChatResponse(
            conversation_id=conv.id,
            response=response_text,
            tools_used=tools_used,
            smoke_alert=smoke_alert,
        )

    def get_messages(self, conversation_id: str) -> list:
        messages = self.store.get_messages(conversation_id)
        return [
            MessageRecord(
                role=m.role,
                content=m.content,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ]

    def _build_history(self, conversation_id: str) -> list:
        messages = self.store.get_messages(conversation_id)
        return [{"role": m.role, "content": m.content} for m in messages]

    def _extract_smoke_alert(self, response_text: str) -> Optional[SmokeAlert]:
        """
        Parse smoke alert JSON from response text if the smoke-detector reported a platform-wide incident.
        Uses raw_decode to correctly handle nested JSON objects.
        """
        try:
            start = response_text.find('{"alert_type"')
            if start == -1:
                return None
            data, _ = json.JSONDecoder().raw_decode(response_text, start)
            if data.get("alert_type") == "platform_wide_incident":
                return SmokeAlert(**data)
        except (json.JSONDecodeError, KeyError, TypeError, ValidationError):
            pass
        return None
