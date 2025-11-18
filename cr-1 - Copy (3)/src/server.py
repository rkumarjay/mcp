from typing import Any
from fastapi import FastAPI, HTTPException, Request, Depends
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)