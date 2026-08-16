"""MCP server exposing SupportIQ's support tools via FastMCP.

Runs as a stdio MCP server process:
    python -m app.mcp_tools.server
"""

from mcp.server.fastmcp import FastMCP

from app.mcp_tools.tools import check_order_status, create_ticket

mcp = FastMCP("supportiq-tools")


@mcp.tool(name="check_order_status")
def check_order_status_tool(order_id: str) -> dict:
    """Check the current status of a customer's order.

    Args:
        order_id: The customer's order ID (digits only).
    """
    return check_order_status(order_id)


@mcp.tool(name="create_ticket")
def create_ticket_tool(issue: str) -> dict:
    """Create a new support ticket for a customer issue.

    Args:
        issue: A short description of the issue to file.
    """
    return create_ticket(issue)


if __name__ == "__main__":
    mcp.run()
