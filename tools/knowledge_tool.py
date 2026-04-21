from pathlib import Path


class KnowledgeTool:
    def __init__(self, knowledge_dir: str = "knowledge"):
        self.knowledge_dir = Path(knowledge_dir)

    def search_known_issues(self, query: str) -> list[str]:
        """Keyword search across all .md files. Returns matching file contents."""
        query_lower = query.lower()
        results = []
        for md_file in self.knowledge_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            if query_lower in content.lower():
                results.append(content)
        return results

    def get_runbook(self, topic: str) -> str:
        """Return content of the first .md file whose name contains topic."""
        topic_lower = topic.lower()
        for md_file in self.knowledge_dir.rglob("*.md"):
            if topic_lower in md_file.stem.lower():
                return md_file.read_text(encoding="utf-8")
        return f"Runbook not found for topic: {topic}"

    def as_tools(self) -> list[dict]:
        """Return Anthropic tool definitions for this tool."""
        return [
            {
                "name": "search_known_issues",
                "description": (
                    "Search the internal knowledge base of known issues and runbooks. "
                    "Use this to check if a symptom matches a previously documented pattern. "
                    "Input is a free-text query."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Symptom or error description to search for"}
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_runbook",
                "description": (
                    "Retrieve a specific runbook by topic name. "
                    "Use this when you have identified a known issue type and need investigation steps."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Topic name, e.g. 'ms_throttling' or 'connector_failure'"}
                    },
                    "required": ["topic"],
                },
            },
        ]

    async def call(self, tool_name: str, tool_input: dict) -> str:
        """Dispatch a tool call by name. Returns result as string."""
        if tool_name == "search_known_issues":
            results = self.search_known_issues(tool_input["query"])
            if not results:
                return "No matching known issues found."
            return "\n\n---\n\n".join(results)
        if tool_name == "get_runbook":
            return self.get_runbook(tool_input["topic"])
        return f"Unknown tool: {tool_name}"
