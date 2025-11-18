from typing import Any
import os
import httpx
from fastapi import FastAPI, HTTPException

# Initialize FastAPI app that will act as a proxy
app = FastAPI(title="hello-client")

# Cloud Run server URL (fallback to local for development)
SERVER_URL = os.getenv("SERVER_URL", "https://mcp-hello-456052106337.us-central1.run.app")

def get_auth_token() -> str:
    """Get ID token for authenticating with the server."""
    import google.auth.transport.requests
    import google.oauth2.id_token

    auth_req = google.auth.transport.requests.Request()
    target_audience = SERVER_URL
    return google.oauth2.id_token.fetch_id_token(auth_req, target_audience)

def call_hello_server(name: str, enable_auth: bool = False) -> dict:
    """Call the hello server endpoint with optional authentication."""
    url = f"{SERVER_URL}/hello?name={name}"
    print(f"Calling server at: {url}")  # Debug print
    
    headers = {}
    if enable_auth:
        # Generate new token if enable_auth is True
        try:
            id_token = get_auth_token()
            print(f"\n[MCP-CLIENT-2] Auth Token: {id_token}\n")  # Print the token with service identifier
            headers = {"Authorization": f"Bearer {id_token}"}
        except Exception as e:
            print(f"[MCP-CLIENT-2] Failed to get auth token: {e}")
    
    with httpx.Client() as client:
        try:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"HTTP error occurred: {e}")  # Debug print
            print(f"Response text: {e.response.text if hasattr(e, 'response') else 'No response'}")  # Debug print
            raise

from fastapi import APIRouter

router = APIRouter()

from pydantic import BaseModel

class NameRequest(BaseModel):
    name: str = "World"
    enable_auth: bool = False

@router.post("/proxy_hello")
def proxy_hello(request: NameRequest) -> dict[str, Any]:
    """
    A proxy endpoint that connects to the hello server and returns its response.
    
    Args:
        request: The request body containing the name and authentication flag
    """
    print(f"Received request with name: {request.name}, auth enabled: {request.enable_auth}")  # Debug print
    try:
        result = call_hello_server(request.name, request.enable_auth)
        print(f"Got result from server: {result}")  # Debug print
        return {
            "proxied_message": result["message"],
            "proxy_info": "Called through client proxy"
        }
    except httpx.HTTPError as e:
        error_msg = str(e)
        # Get the status code from the response if available
        status_code = e.response.status_code if getattr(e, "response", None) is not None else 500

        # Safely parse upstream error: try JSON first, then fall back to plain text
        upstream_error: Any
        if getattr(e, "response", None) is not None:
            try:
                upstream_error = e.response.json()
            except Exception:
                upstream_error = {"text": e.response.text}
        else:
            upstream_error = {"detail": error_msg}
        
        print(f"Error occurred: {error_msg}")  # Debug print
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": f"Failed to call hello server: {error_msg}",
                "status": "error",
                "upstream_error": upstream_error
            }
        )
    except Exception as e:
        error_msg = str(e)
        print(f"Error occurred: {error_msg}")  # Debug print
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Internal server error: {error_msg}",
                "status": "error"
            }
        )

# Include the router in the main app
app.include_router(router, prefix="/api/v1")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)