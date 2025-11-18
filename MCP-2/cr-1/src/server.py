from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import json
from jsonrpcserver import method, async_dispatch, Success
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
# MCP JSON-RPC 2.0 endpoint (using jsonrpcserver)
# -----------------------------

@method(name="initialize")
async def mcp_initialize() -> Any:
    return Success({
        "serverName": "mcp-hello",
        "protocolVersion": "1.0",
        "capabilities": {"tools": True},
    })


@method(name="ping")
async def mcp_ping() -> Any:
    return Success({"status": "ok"})


@method(name="tools/list")
async def mcp_tools_list() -> Any:
    tools = [
        {
            "name": "hello",
            "description": "Greets a name with a friendly message",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Name to greet"}},
                "required": ["name"],
            },
        }
    ]
    return Success({"tools": tools})


@method(name="tools/call")
async def mcp_tools_call(tool: str, name: str = "World") -> Any:
    if tool == "hello":
        return Success({"message": f"Hello, {name}!", "type": "greeting"})
    # Tool not found -> raise a generic error, jsonrpcserver will format it as an error response
    raise ValueError(f"Tool not found: {tool}")


@app.post("/mcp", dependencies=[Depends(verify_token)])
async def mcp_endpoint(http_request: Request):
    try:
        body = await http_request.json()
    except Exception as e:
        # jsonrpcserver will format proper error if we pass invalid JSON, but ensure dict here
        return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error", "data": {"detail": str(e)}}}, status_code=200)

    # Log for observability
    try:
        print(f"[MCP-SERVER] Received MCP method={body.get('method')} id={body.get('id')} params={body.get('params')}")
    except Exception:
        pass

    # jsonrpcserver expects a JSON string in this version
    response = await async_dispatch(json.dumps(body))
    # jsonrpcserver may return a Response object, a dict, or a string.
    try:
        if isinstance(response, dict):
            return JSONResponse(content=response, status_code=200)
        if isinstance(response, bytes):
            return JSONResponse(content=json.loads(response.decode("utf-8")), status_code=200)
        if isinstance(response, str):
            return JSONResponse(content=json.loads(response), status_code=200)
        # Fallback to string conversion
        return JSONResponse(content=json.loads(str(response)), status_code=200)
    except Exception:
        # As a last resort, return the stringified response
        return JSONResponse(content={"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32603, "message": "Internal error", "data": str(response)}}, status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)