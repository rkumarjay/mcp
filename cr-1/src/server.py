from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import Response
import uvicorn
from google.auth.transport import requests
import google.oauth2.id_token
import json

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
        
        # Optional: Application-level service account restriction
        # Uncomment the following lines if you want to restrict at application level
        # instead of relying solely on Cloud Run IAM policy
        # allowed_service_accounts = [
        #     "mcp-client-sa@ai-10292025.iam.gserviceaccount.com"
        # ]
        # caller_email = decoded_token.get("email")
        # if caller_email not in allowed_service_accounts:
        #     raise HTTPException(
        #         status_code=403, 
        #         detail=f"Access denied for service account: {caller_email}"
        #     )
        
        # Log cal ity details for diagnostics
        # IAM policy at Cloud Run level controls which service accounts can invoke this service
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
# MCP endpoint with manual JSON-RPC handling
# -----------------------------

# Mount MCP server into FastAPI with auth dependency
@app.post("/mcp", dependencies=[Depends(verify_token)])
async def mcp_endpoint(request: Request):
    """MCP endpoint with authentication - handles JSON-RPC 2.0 requests."""
    try:
        body = await request.json()
        print(f"[MCP-SERVER] Received MCP method={body.get('method')} id={body.get('id')} params={body.get('params')}")
        
        # Handle different MCP methods
        method = body.get("method")
        params = body.get("params", {})
        msg_id = body.get("id")
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "mcp-hello",
                    "version": "1.0.0"
                }
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "hello",
                        "description": "Greets a name with a friendly message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name to greet"
                                }
                            }
                        }
                    }
                ]
            }
        elif method == "tools/call":
            tool_name = params.get("tool")
            if tool_name == "hello":
                name = params.get("name", "World")
                # Return the result directly as the old format expected
                result = {"message": f"Hello, {name}!", "type": "greeting"}
            else:
                return Response(
                    content=json.dumps({
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }),
                    media_type="application/json"
                )
        else:
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }),
                media_type="application/json"
            )
        
        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result
        }
        
        return Response(content=json.dumps(response), media_type="application/json")
        
    except Exception as e:
        print(f"[MCP-SERVER] Error: {e}")
        return Response(
            content=json.dumps({
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }),
            media_type="application/json"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)