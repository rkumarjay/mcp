from typing import Any
from fastapi import FastAPI
import uvicorn

# Initialize FastAPI server
app = FastAPI(title="hello-server")

@app.get("/hello")
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