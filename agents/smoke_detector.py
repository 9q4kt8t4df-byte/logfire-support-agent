# agents/smoke_detector.py
import config as cfg
from agents.base import BaseAgent
from tools.logfire_tool import LogfireTool
from tools.cross_tenant import CrossTenantTool


class SmokeDetectorAgent(BaseAgent):
    def __init__(self, logfire_tool: LogfireTool, cross_tenant_tool: CrossTenantTool) -> None:
        super().__init__(
            agent_id="smoke-detector",
            config=cfg.AGENTS["smoke-detector"],
            tools=[logfire_tool, cross_tenant_tool],
        )
