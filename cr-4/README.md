# MCP Server as Google Cloud Function (cr-4)

This is a minimal Model Context Protocol (MCP) server implemented as a Google Cloud Function (Gen 2) over HTTP. It supports:

- initialize
- tools/list
- tools/call (with either spec params `{ name, arguments }` or the legacy shape `{ tool, name }` used in `cr-2`)

It returns MCP-style `result.content[0].text` with a JSON payload matching the prior projects.

The endpoint is designed to be compatible with:
- The direct HTTP client in `cr-3` (`/api/v1/mcp_call`), which calls `initialize` + `tools/call` via POST JSON.
- LangGraph's `MCPServerClient` (over HTTP per-request). If your LangGraph client expects SSE transport, prefer Cloud Run instead. For Cloud Functions, this HTTP JSON-RPC style is reliable.

## Files

- `main.py` — Cloud Function entry point `mcp_function` handling JSON-RPC over HTTP.
- `requirements.txt` — Runtime deps (Functions Framework + Google Auth for optional token verification).

## Local run

You can run locally using the Functions Framework.

```bash
# From cr-4 folder
pip install -r requirements.txt
functions-framework --target mcp_function --port 8080
```

Then in another shell:

```bash
# initialize
curl -sS -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name":"local","version":"0"}}
  }'

# tools/call (spec shape)
curl -sS -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {"name": "hello", "arguments": {"name": "World"}}
  }'

# tools/call (legacy shape — matches cr-2)
curl -sS -X POST http://127.0.0.1:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {"tool": "hello", "name": "World"}
  }'
```

Note: The function accepts requests on any path; `/mcp` is used by convention in the examples.

## Auth (optional)

If you deploy behind IAM or want to require Google-issued ID tokens:

- Set env var `REQUIRE_AUTH=true`
- Optionally set `AUTH_AUDIENCE` to the expected audience (e.g., your Cloud Run URL or custom domain)

The function expects `Authorization: Bearer <token>` and will verify it.

## Deploy to Google Cloud Functions (Gen 2)

Assumes you have `gcloud` configured with your project and region. Replace placeholders as needed.

```bash
# From cr-4 folder
# Create a Python 3.11 HTTP function
gcloud functions deploy mcp-hello-func \
  --gen2 \
  --region=us-central1 \
  --runtime=python311 \
  --entry-point=mcp_function \
  --trigger-http \
  --allow-unauthenticated

# If you want to require auth instead:
# Add: --set-env-vars REQUIRE_AUTH=true,AUTH_AUDIENCE=https://<your-url>
```

After deploy, update `SERVER_URL` in `cr-3` (if needed) to point to the function URL and test with `/api/v1/mcp_call`.

## Using from LangGraph MCP client

In `cr-3`, the `call_mcp_server` function already uses direct HTTP JSON-RPC and will work with this function.

The experimental `MCPServerClient` path in `cr-3` attempts SSE transport which is better suited to Cloud Run. For Cloud Functions, prefer the HTTP JSON-RPC approach. If your LangGraph version supports HTTP/non-SSE transport, configure it with the function URL and omit SSE.

## Notes

- Cloud Functions (Gen 2) run on Cloud Run, but the Functions Framework for Python doesn’t natively support WebSockets/SSE in the same way a custom ASGI server does. That’s why this implementation uses stateless HTTP JSON-RPC calls per request.
- If you need streaming or bi-directional MCP transports, deploy the server in `cr-1` (FastMCP SSE) to Cloud Run instead.
