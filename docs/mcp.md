# AEGIS MCP server

The AEGIS data portal is available as a Model Context Protocol (MCP) server so
that LLM clients (Claude Desktop and others) can search species, retrieve
samples, generate bulk-download commands, and read the downloader documentation
directly inside a chat.

- **Endpoint:** `https://portal.aegisearth.bio/api/mcp/` (trailing slash recommended)
- **Transport:** Streamable HTTP (MCP spec 2025-03-26)
- **Auth:** none (public read-only)

Hitting `/api/mcp` without the trailing slash returns a 307 redirect to
`/api/mcp/`. Modern HTTP clients (including Claude Desktop) preserve POST
method and body across 307, so either URL works, but `/api/mcp/` is the
canonical form.

## Tools

| Tool | What it does |
|---|---|
| `search_species` | Filter the data portal by phylogeny, status, country, free text. |
| `get_species` | Full record for one `tax_id`. |
| `search_samples` | Filter the samples index by tax_id, country, organism part, etc. |
| `get_sample` | Full record for one BioSamples accession. |
| `aggregate_samples_by_location` | Geo-grid cluster counts for a map view. |
| `build_bulk_download_command` | Render the exact `aegis-download` CLI command for the user's filters. |

## Resources

| URI | Content |
|---|---|
| `bulk-downloader://readme` | Full `aegis-download` README (install, flags, output layout). |

## Connecting Claude Desktop

1. Open Claude Desktop.
2. **Settings → Connectors → Add custom connector → Remote MCP server**.
3. Set the URL to `https://portal.aegisearth.bio/api/mcp/`. Leave auth blank.
4. Save and restart Claude Desktop.
5. The six tools appear in the tool picker; you can call them from any chat.

## Fallback: `mcp-remote`

If your client doesn't yet support remote Streamable HTTP, use the `mcp-remote`
stdio→HTTP proxy:

```json
{
  "mcpServers": {
    "aegis": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://portal.aegisearth.bio/api/mcp/"]
    }
  }
}
```

Drop that into your client's MCP servers config and restart.

## Local development

To exercise the MCP server against a local BE:

```bash
cd be
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080
# In another shell, point a client at:
#   http://localhost:8080/api/mcp/
```

## Quick smoke test (curl)

```bash
curl -i -X POST https://portal.aegisearth.bio/api/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0.0"}}}'
```

Expected response: HTTP 200, an `Mcp-Session-Id` response header, and a JSON-RPC
result body listing the server's tool/resource capabilities.
