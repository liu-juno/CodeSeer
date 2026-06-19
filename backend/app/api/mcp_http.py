from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.mcp_tokens import verify_token
from app.api.mcp_tools import TOOLS, KNOWN_TOOLS
from app.api.mcp_handlers import TOOL_HANDLERS

router = APIRouter(prefix="/mcp/http", tags=["mcp-http"])

_TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "aicode" / "templates"


def _err(code: int, msg: str, req_id) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}


def _load_initialize_instructions() -> str:
    p = _TEMPLATES_DIR / "initialize_instructions.md"
    return p.read_text(encoding="utf-8") if p.exists() else "已连接 CodeSeer 平台。"


async def _authenticate(authorization: Optional[str], db: AsyncSession):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization[len("Bearer "):]
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


@router.post("")
async def mcp_http_endpoint(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """MCP HTTP 端点：JSON-RPC 2.0 over HTTP"""
    user = await _authenticate(authorization, db)

    body = await request.json()
    method = body.get("method", "")
    req_id = body.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "codeseer", "version": "1.0.0"},
                "instructions": _load_initialize_instructions(),
            },
        }

    if method in ("notifications/initialized", "initialized"):
        return {}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        params = body.get("params")
        if params is None:
            return _err(-32602, "Missing params", req_id)

        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if tool_name not in KNOWN_TOOLS:
            return _err(-32601, f"Unknown tool: {tool_name}", req_id)

        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            return _err(-32601, f"Tool not implemented: {tool_name}", req_id)

        result = await handler(arguments, user, db)

        if result is None:
            return _err(-32602, f"Missing required argument for {tool_name}", req_id)
        if result.get("__not_found__"):
            return _err(-32602, "Resource not found", req_id)

        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    return _err(-32601, f"Method not found: {method}", req_id)
