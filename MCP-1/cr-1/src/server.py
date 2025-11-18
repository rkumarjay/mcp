from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, Depends
import json
import uvicorn
from google.auth.transport import requests
import google.oauth2.id_token

# Initialize FastAPI server
app = FastAPI(title="hello-server")

async def verify_token(request: Request):
    """Verify the incoming ID token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")
    
    token = auth_header.split("Bearer ")[1]
    try:
        # Initialize the Requests object
        request = requests.Request()
        
        # Verify the ID token
        decoded_token = google.oauth2.id_token.verify_oauth2_token(
            token, request)
        
        # Verify the token's audience matches our service
        if decoded_token.get("aud") != "https://mcp-hello-456052106337.us-central1.run.app":
            raise ValueError("Invalid token audience")
        
        # Log caller identity details for diagnostics
        try:
            caller_email = decoded_token.get("email")
            caller_sub = decoded_token.get("sub")
            caller_iss = decoded_token.get("iss")
            caller_aud = decoded_token.get("aud")
            print(
                f"[MCP-SERVER] Caller email={caller_email} sub={caller_sub} iss={caller_iss} aud={caller_aud}"
            )
        except Exception as log_e:
            print(f"[MCP-SERVER] Failed to log token claims: {log_e}")
            
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

@app.get("/hello", dependencies=[Depends(verify_token)])
def say_hello(name: str = "World") -> dict[str, Any]:
    """
    A simple greeting endpoint that returns hello message.
    
    Args:
        name: The name to greet (optional)
    """
    return {
        "message": f"Hello, {name}!",
        "type": "greeting"
    }

# -----------------------------
# MCP JSON-RPC 2.0 endpoint
# -----------------------------

def _jsonrpc_success(id_value: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_value, "result": result}


def _jsonrpc_error(id_value: Any, code: int, message: str, data: Any | None = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_value, "error": err}


@app.post("/mcp", dependencies=[Depends(verify_token)])
async def mcp_endpoint(http_request: Request) -> Dict[str, Any]:
    """Minimal MCP handler over JSON-RPC 2.0.

    Supported methods:
      - initialize
      - ping
      - tools/list
      - tools/call (params: { tool: "hello", name: str })
    """
    try:
        body = await http_request.body()
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        return _jsonrpc_error(None, -32700, "Parse error", {"detail": str(e)})

    jsonrpc = payload.get("jsonrpc")
    method = payload.get("method")
    id_value = payload.get("id")
    params = payload.get("params", {}) or {}

    if jsonrpc != "2.0":
        return _jsonrpc_error(id_value, -32600, "Invalid Request", {"reason": "jsonrpc version must be '2.0'"})

    print(f"[MCP-SERVER] Received MCP method={method} id={id_value} params={params}")

    try:
        if method == "initialize":
            result = {
                "serverName": "mcp-hello",
                "protocolVersion": "1.0",
                "capabilities": {"tools": True},
            }
            return _jsonrpc_success(id_value, result)

        if method == "ping":
            return _jsonrpc_success(id_value, {"status": "ok"})

        if method == "tools/list":
            tools = [
                {
                    "name": "hello",
                    "description": "Greets a name with a friendly message",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name to greet"}
                        },
                        "required": ["name"],
                    },
                }
            ]
            return _jsonrpc_success(id_value, {"tools": tools})

        if method == "tools/call":
            tool = params.get("tool")
            if tool == "hello":
                name = params.get("name", "World")
                greeting = {"message": f"Hello, {name}!", "type": "greeting"}
                return _jsonrpc_success(id_value, greeting)
            else:
                return _jsonrpc_error(id_value, -32601, "Tool not found", {"tool": tool})

        # Method not found
        return _jsonrpc_error(id_value, -32601, "Method not found", {"method": method})

    except Exception as e:
        return _jsonrpc_error(id_value, -32603, "Internal error", {"detail": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)