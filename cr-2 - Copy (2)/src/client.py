from typing import Any
import os
import httpx
from fastapi import FastAPI

# Initialize FastAPI app that will act as a proxy
app = FastAPI(title="hello-client")

# Cloud Run server URL (fallback to local for development)
SERVER_URL = os.getenv("SERVER_URL", "https://mcp-hello-456052106337.us-central1.run.app")

def call_hello_server(name: str) -> dict:
    """Call the hello server endpoint."""
    url = f"{SERVER_URL}/hello?name={name}"
    print(f"Calling server at: {url}")  # Debug print
    with httpx.Client() as client:
        try:
            response = client.get(url)
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

@router.post("/proxy_hello")
def proxy_hello(request: NameRequest) -> dict[str, Any]:
    """
    A proxy endpoint that connects to the hello server and returns its response.
    
    Args:
        request: The request body containing the name to send to the hello server
    """
    print(f"Received request with name: {request.name}")  # Debug print
    try:
        result = call_hello_server(request.name)
        print(f"Got result from server: {result}")  # Debug print
        return {
            "proxied_message": result["message"],
            "proxy_info": "Called through client proxy"
        }
    except Exception as e:
        error_msg = str(e)
        print(f"Error occurred: {error_msg}")  # Debug print
        return {
            "error": f"Failed to call hello server: {error_msg}",
            "status": "error"
        }

# Include the router in the main app
app.include_router(router, prefix="/api/v1")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)