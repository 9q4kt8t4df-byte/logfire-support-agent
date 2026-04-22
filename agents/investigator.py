# agents/investigator.py
from __future__ import annotations
import config as cfg
from agents.base import BaseAgent
from tools.logfire_tool import LogfireTool
from tools.knowledge_tool import KnowledgeTool


class InvestigatorAgent(BaseAgent):
    def __init__(self, logfire_tool: LogfireTool, knowledge_tool: KnowledgeTool) -> None:
        super().__init__(
            agent_id="logfire-investigator",
            config=cfg.AGENTS["logfire-investigator"],
            tools=[logfire_tool, knowledge_tool],
        )
