"""MCP client that talks to the local SupportIQ tools server over stdio."""

import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult


def _format_result(result: CallToolResult) -> str:
    if getattr(result, "structuredContent", None) is not None:
        return json.dumps(result.structuredContent, default=str)
    texts = [block.text for block in result.content if hasattr(block, "text")]
    return "\n".join(texts) if texts else str(result)


async def call_tool(name: str, arguments: dict) -> str:
    """Call an MCP tool on the SupportIQ server and return a JSON string result."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_tools.server"],
        env={**os.environ},
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            return _format_result(result)
