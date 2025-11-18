import json
import os
from typing import Any, Dict

from flask import Request, Response

# Optional: enable ID token verification by setting REQUIRE_AUTH=true
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() in {"1", "true", "yes"}

# Basic server info/capabilities for MCP initialize
SERVER_INFO = {"name": "mcp-hello-func", "version": "1.0.0"}
CAPABILITIES = {
    # We support calling tools via HTTP per-request (stateless)
    "tools": {"listChanged": False}
}


def _json_response(payload: Dict[str, Any], status: int = 200) -> Response:
    return Response(
        json.dumps(payload), status=status, mimetype="application/json; charset=utf-8"
    )


def _verify_auth(request: Request) -> None:
    """Optionally verify Google ID token in Authorization header.

    Expects: Authorization: Bearer <token>
    Raises: ValueError if verification fails.
    """
    if not REQUIRE_AUTH:
        return

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise ValueError("missing bearer token")

    token = auth_header.split(" ", 1)[1]

    # Audience: if you front this function behind a Cloud Run custom domain, set to that URL.
    audience = os.getenv("AUTH_AUDIENCE")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as ga_requests

        req = ga_requests.Request()
        # If audience is None, library will accept any Google-issued token; better to set it.
        id_token.verify_oauth2_token(token, req, audience=audience)
    except Exception as e:
        raise ValueError(f"token verification failed: {e}")


def _rpc_error(id_val: Any, code: int, message: str, data: Any | None = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"jsonrpc": "2.0", "id": id_val, "error": {"code": code, "message": message}}
    if data is not None:
        err["error"]["data"] = data
    return err


def _rpc_result(id_val: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_val, "result": result}


# Our single demo tool
TOOLS = [
    {
        "name": "hello",
        "description": "Greets a name with a friendly message.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "default": "World"}},
            "required": [],
            "additionalProperties": False,
        },
    }
]


def _call_hello(arguments: Dict[str, Any]) -> Dict[str, Any]:
    name = str(arguments.get("name", "World"))
    # MCP "text" content form; clients in cr-2/cr-3 parse this
    payload = {"message": f"Hello, {name}!", "type": "greeting"}
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload),
            }
        ]
    }


def mcp_function(request: Request) -> Response:
    """Google Cloud Function HTTP entrypoint implementing minimal MCP over HTTP.

    Supported JSON-RPC methods:
      - initialize
      - tools/list
      - tools/call  (accepts either {name, arguments} or legacy {tool, name})
    """
    # Optional auth
    try:
        _verify_auth(request)
    except ValueError as e:
        return _json_response({"error": str(e)}, status=401)

    # Only JSON POSTs
    if request.method != "POST":
        return _json_response({"error": "POST required"}, status=405)

    try:
        body = request.get_json(force=True, silent=False)
    except Exception:
        return _json_response({"error": "invalid JSON"}, status=400)

    if not isinstance(body, dict):
        return _json_response({"error": "JSON-RPC object required"}, status=400)

    jsonrpc = body.get("jsonrpc")
    method = body.get("method")
    id_val = body.get("id")
    params = body.get("params", {}) or {}

    if jsonrpc != "2.0":
        return _json_response(_rpc_error(id_val, -32600, "Invalid Request: jsonrpc must be '2.0'"), status=400)

    # initialize handshake
    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": CAPABILITIES,
            "serverInfo": SERVER_INFO,
        }
        return _json_response(_rpc_result(id_val, result))

    # list tools (optional convenience)
    if method in {"tools/list", "tools.list"}:
        return _json_response(_rpc_result(id_val, {"tools": TOOLS}))

    # tools/call
    if method in {"tools/call", "tools.call"}:
        # Accept both MCP spec shape and older client from cr-2
        # Spec: { name: "hello", arguments: { name: "World" } }
        # Legacy: { tool: "hello", name: "World" }
        tool_name = params.get("name") or params.get("tool")
        if tool_name != "hello":
            return _json_response(_rpc_error(id_val, -32601, f"Unknown tool: {tool_name}"), status=404)

        arguments: Dict[str, Any] = params.get("arguments") or {}
        if not arguments and "name" in params and "tool" in params:
            # legacy form from cr-2
            arguments = {"name": params.get("name")}

        try:
            result = _call_hello(arguments)
            return _json_response(_rpc_result(id_val, result))
        except Exception as e:
            return _json_response(_rpc_error(id_val, -32000, "Tool execution failed", {"error": str(e)}), status=500)

    # Unknown method
    return _json_response(_rpc_error(id_val, -32601, f"Method not found: {method}"), status=404)
