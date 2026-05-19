import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    path="/mcp",
    title="MCP - AEGIS",
)


MCP_ENDPOINT = "https://portal.aegisearth.bio/api/mcp/"
MCP_SPEC_URL = "https://modelcontextprotocol.io"
MCP_CLIENTS_URL = "https://modelcontextprotocol.io/clients"
REPO_URL = "https://github.com/EMBL-EBI-ABC/AEGIS"
MCP_REMOTE_NPM_URL = "https://www.npmjs.com/package/mcp-remote"


def _section_heading(text: str) -> html.H2:
    return html.H2(
        text,
        style={
            "fontFamily": "var(--font-display)",
            "fontSize": "1.5rem",
            "color": "var(--aegis-text-primary)",
            "marginTop": "2.5rem",
            "marginBottom": "0.75rem",
        },
    )


def _code_block(text: str) -> html.Pre:
    return html.Pre(
        html.Code(text),
        style={
            "background": "var(--aegis-bg-elevated)",
            "color": "var(--aegis-text-primary)",
            "border": "1px solid var(--aegis-border-subtle)",
            "borderRadius": "var(--radius-md)",
            "padding": "1rem 1.25rem",
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85rem",
            "lineHeight": "1.5",
            "overflowX": "auto",
            "marginBottom": "1rem",
        },
    )


def _inline_code(text: str) -> html.Code:
    return html.Code(
        text,
        style={
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85em",
            "color": "var(--aegis-accent-primary)",
            "background": "var(--aegis-bg-elevated)",
            "padding": "0.1rem 0.35rem",
            "borderRadius": "3px",
        },
    )


def _info_card(label: str, value, link: str | None = None) -> html.Div:
    value_el = html.Code(
        value,
        style={
            "color": "var(--aegis-accent-primary)",
            "fontFamily": "var(--font-mono)",
            "fontSize": "0.85rem",
            "wordBreak": "break-all",
        },
    )
    if link:
        value_el = html.A(
            value_el,
            href=link,
            target="_blank",
            rel="noopener noreferrer",
            style={"textDecoration": "underline", "textUnderlineOffset": "3px"},
        )

    return html.Div(
        [
            html.Div(
                label,
                style={
                    "fontSize": "0.75rem",
                    "color": "var(--aegis-text-muted)",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginBottom": "0.25rem",
                },
            ),
            value_el,
        ],
        style={
            "padding": "1rem",
            "background": "var(--aegis-bg-card)",
            "borderRadius": "var(--radius-md)",
            "border": "1px solid var(--aegis-border-subtle)",
            "textAlign": "center",
        },
    )


def _table_row(left, right) -> html.Tr:
    return html.Tr(
        [
            html.Td(
                left,
                style={
                    "verticalAlign": "top",
                    "padding": "0.55rem 0.75rem",
                    "whiteSpace": "nowrap",
                },
            ),
            html.Td(
                right,
                style={
                    "verticalAlign": "top",
                    "padding": "0.55rem 0.75rem",
                    "color": "var(--aegis-text-secondary)",
                },
            ),
        ]
    )


_TOOLS = [
    (
        "search_species",
        "Search the data portal for species records — filter by phylogeny (kingdom, order, family), pipeline status, country, or free-text query. Returns paginated results plus aggregation counts.",
    ),
    (
        "get_species",
        "Fetch the full data portal record for one species by NCBI tax_id. Includes every assembly, annotation bundle, raw-data run, and aggregated sample provenance.",
    ),
    (
        "search_samples",
        "Search the BioSamples index — filter by taxId, country, organism part, sex, collecting institution, or free-text query.",
    ),
    (
        "get_sample",
        "Fetch the full sample record for one BioSamples accession.",
    ),
    (
        "aggregate_samples_by_location",
        "Aggregate samples into geographic clusters at a chosen zoom level. Useful for map views and for answering 'where were samples concentrated?' questions.",
    ),
    (
        "build_bulk_download_command",
        "Render the exact aegis-download shell command for a set of filters. The model can use this to hand the user a ready-to-run CLI invocation that downloads the matching data locally.",
    ),
]


_RESOURCES = [
    (
        "bulk-downloader://readme",
        "Full aegis-download CLI documentation (install, flags, output layout, exit codes). Served on demand so the model can answer questions about the CLI without external lookups.",
    ),
]


_MCP_REMOTE_CONFIG = """{
  "mcpServers": {
    "aegis": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://portal.aegisearth.bio/api/mcp/"]
    }
  }
}"""


_CURL_TEST = """curl -i -X POST https://portal.aegisearth.bio/api/mcp/ \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json, text/event-stream" \\
  --data-binary @- <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0.0"}}}
EOF"""


layout = html.Div(
    [
        # Header
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    html.Div(
                        [
                            html.H1(
                                "MCP Server",
                                style={
                                    "fontFamily": "var(--font-display)",
                                    "fontSize": "2.5rem",
                                    "color": "var(--aegis-text-primary)",
                                    "marginBottom": "0.5rem",
                                },
                            ),
                            html.P(
                                [
                                    "The AEGIS data portal is also available as a ",
                                    html.A(
                                        "Model Context Protocol",
                                        href=MCP_SPEC_URL,
                                        target="_blank",
                                        rel="noopener noreferrer",
                                        style={
                                            "color": "var(--aegis-accent-primary)",
                                            "textDecoration": "underline",
                                            "textUnderlineOffset": "3px",
                                        },
                                    ),
                                    " (MCP) server, so any MCP-aware LLM client can search species, retrieve samples, and generate bulk-download commands directly from a chat.",
                                ],
                                style={
                                    "color": "var(--aegis-text-muted)",
                                    "marginBottom": "0",
                                },
                            ),
                        ],
                        className="pt-4 pb-3",
                    ),
                ),
            ),
        ),
        # Info cards
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(_info_card("Endpoint", MCP_ENDPOINT), md=5, className="mb-3"),
                    dbc.Col(_info_card("Transport", "Streamable HTTP"), md=4, className="mb-3"),
                    dbc.Col(_info_card("Auth", "None (public read-only)"), md=3, className="mb-3"),
                ],
                className="mb-4",
            ),
        ),
        # Body
        dbc.Container(
            [
                _section_heading("What is MCP?"),
                html.P(
                    [
                        "The ",
                        html.A(
                            "Model Context Protocol",
                            href=MCP_SPEC_URL,
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                        ),
                        " is an open standard for exposing tools and data sources to LLMs. An MCP-aware client (assistant app, IDE plugin, agent framework) connects to an MCP server, lists the available tools, and lets the model call them as part of a conversation. AEGIS implements the spec's ",
                        _inline_code("2025-03-26"),
                        " Streamable HTTP transport, so any compatible client can reach the endpoint over plain HTTPS.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                html.P(
                    [
                        "For a list of clients that speak MCP, see ",
                        html.A(
                            "modelcontextprotocol.io/clients ↗",
                            href=MCP_CLIENTS_URL,
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                        ),
                        ".",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _section_heading("Tools"),
                html.P(
                    "The server exposes six tools. Each is hand-written so the model gets useful descriptions of when to call it and what to do with the result.",
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                html.Div(
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("Tool", style={"width": "32%"}),
                                        html.Th("What it does"),
                                    ]
                                )
                            ),
                            html.Tbody(
                                [_table_row(_inline_code(name), desc) for name, desc in _TOOLS]
                            ),
                        ],
                        striped=True,
                        bordered=False,
                        hover=True,
                        responsive=True,
                    ),
                    style={
                        "background": "var(--aegis-bg-elevated)",
                        "borderRadius": "var(--radius-md)",
                        "border": "1px solid var(--aegis-border-subtle)",
                        "overflow": "hidden",
                    },
                ),
                _section_heading("Resources"),
                html.P(
                    "MCP resources are static documents the model can request on demand.",
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                html.Div(
                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th("URI", style={"width": "32%"}),
                                        html.Th("Content"),
                                    ]
                                )
                            ),
                            html.Tbody(
                                [_table_row(_inline_code(uri), desc) for uri, desc in _RESOURCES]
                            ),
                        ],
                        striped=True,
                        bordered=False,
                        hover=True,
                        responsive=True,
                    ),
                    style={
                        "background": "var(--aegis-bg-elevated)",
                        "borderRadius": "var(--radius-md)",
                        "border": "1px solid var(--aegis-border-subtle)",
                        "overflow": "hidden",
                    },
                ),
                _section_heading("Connecting a client"),
                html.P(
                    [
                        "Most MCP clients accept a remote server in one of two forms: a direct Streamable HTTP URL, or a stdio command that proxies to one. Use whichever your client supports — the underlying server is the same.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                html.H3(
                    "Native Streamable HTTP",
                    style={
                        "fontFamily": "var(--font-display)",
                        "fontSize": "1.15rem",
                        "color": "var(--aegis-text-primary)",
                        "marginTop": "1.5rem",
                        "marginBottom": "0.5rem",
                    },
                ),
                html.P(
                    [
                        "If your client has a 'Remote MCP server' or 'Custom connector' option, paste the endpoint URL: ",
                        _inline_code(MCP_ENDPOINT),
                        ". Leave authentication blank.",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                html.P(
                    [
                        "Note that ",
                        _inline_code("/api/mcp"),
                        " without the trailing slash returns a 307 redirect to ",
                        _inline_code("/api/mcp/"),
                        ". Modern HTTP clients preserve POST method and body across 307, but using the trailing-slash form avoids the round-trip.",
                    ],
                    style={"color": "var(--aegis-text-muted)", "fontSize": "0.9rem"},
                ),
                html.H3(
                    "stdio bridge via mcp-remote",
                    style={
                        "fontFamily": "var(--font-display)",
                        "fontSize": "1.15rem",
                        "color": "var(--aegis-text-primary)",
                        "marginTop": "1.5rem",
                        "marginBottom": "0.5rem",
                    },
                ),
                html.P(
                    [
                        "Clients that only speak stdio MCP (or whose native remote support requires OAuth) can use ",
                        html.A(
                            _inline_code("mcp-remote"),
                            href=MCP_REMOTE_NPM_URL,
                            target="_blank",
                            rel="noopener noreferrer",
                            style={"textDecoration": "underline", "textUnderlineOffset": "3px"},
                        ),
                        ", an npm shim that proxies stdio to a remote Streamable HTTP server. Add this to your client's MCP config (the exact filename varies by client — common examples are ",
                        _inline_code("claude_desktop_config.json"),
                        ", ",
                        _inline_code("settings.json"),
                        ", or a project-local ",
                        _inline_code(".mcp.json"),
                        "):",
                    ],
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block(_MCP_REMOTE_CONFIG),
                html.P(
                    [
                        "Requires ",
                        _inline_code("npx"),
                        " (ships with Node.js). Restart the client after editing the config.",
                    ],
                    style={"color": "var(--aegis-text-muted)", "fontSize": "0.9rem"},
                ),
                _section_heading("Quick test"),
                html.P(
                    "Verify the server is reachable from the command line — sends a JSON-RPC initialize and expects a 200 with an Mcp-Session-Id header in response.",
                    style={"color": "var(--aegis-text-secondary)"},
                ),
                _code_block(_CURL_TEST),
                _section_heading("Source"),
                html.Ul(
                    [
                        html.Li(
                            html.A(
                                "Server implementation on GitHub ↗",
                                href=f"{REPO_URL}/blob/main/be/mcp_server.py",
                                target="_blank",
                                rel="noopener noreferrer",
                                style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                            ),
                            style={"marginBottom": "0.4rem"},
                        ),
                        html.Li(
                            html.A(
                                "MCP specification ↗",
                                href=MCP_SPEC_URL,
                                target="_blank",
                                rel="noopener noreferrer",
                                style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                            ),
                            style={"marginBottom": "0.4rem"},
                        ),
                        html.Li(
                            [
                                "Report issues: ",
                                html.A(
                                    f"{REPO_URL}/issues ↗",
                                    href=f"{REPO_URL}/issues",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    style={"color": "var(--aegis-accent-primary)", "textDecoration": "underline"},
                                ),
                            ],
                            style={"marginBottom": "0.4rem"},
                        ),
                    ],
                    style={"paddingLeft": "1.25rem"},
                ),
            ],
            className="pb-5",
        ),
    ]
)
