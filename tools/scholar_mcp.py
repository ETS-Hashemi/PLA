#!/usr/bin/env python3
"""Scholar MCP server: Semantic Scholar + Scopus search as Claude tools.

A minimal Model Context Protocol server (stdio, newline-delimited
JSON-RPC, no dependencies beyond the standard library) exposing two
tools to any MCP client:

- search_semantic_scholar(query, limit): Semantic Scholar Graph API;
  returns title, authors, venue, year, DOI, and open-access PDF URL.
- search_scopus(query, limit): Scopus Search API (TITLE-ABS-KEY);
  returns title, first author, venue, volume/issue/pages, year, DOI.

Keys come from the environment: S2_API_KEY and SCOPUS_API_KEY. A tool
whose key is missing reports that instead of failing the server, so
you can register the server with only one key.

Register once for every Claude Code conversation on this machine:

    claude mcp add --scope user scholar \
      -e S2_API_KEY=your-s2-key -e SCOPUS_API_KEY=your-scopus-key \
      -- python3 /absolute/path/to/scholar_mcp.py

or for Claude Desktop, add to claude_desktop_config.json:

    "scholar": {
      "command": "python3",
      "args": ["/absolute/path/to/scholar_mcp.py"],
      "env": {"S2_API_KEY": "...", "SCOPUS_API_KEY": "..."}
    }

Never hard-code keys in this file or commit them anywhere.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "search_semantic_scholar",
        "description": (
            "Search academic literature via the Semantic Scholar Graph "
            "API. Returns title, authors, venue, year, DOI, and an "
            "open-access PDF link when one exists. Good for CS/ML "
            "coverage and finding free PDFs."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "Search query (title words, "
                                         "topic, author names)"},
                "limit": {"type": "integer", "default": 5,
                          "minimum": 1, "maximum": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_scopus",
        "description": (
            "Search the Scopus (Elsevier) index via a TITLE-ABS-KEY "
            "query. Returns title, first author, venue with "
            "volume/issue/pages, year, and DOI. Authoritative journal "
            "coverage; supports Scopus field syntax like AND/OR and "
            "quoted phrases."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "Scopus query; quoted phrases "
                                         "and AND/OR allowed"},
                "limit": {"type": "integer", "default": 5,
                          "minimum": 1, "maximum": 25},
            },
            "required": ["query"],
        },
    },
]


def _get(url, headers):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def semantic_scholar(query, limit):
    key = os.environ.get("S2_API_KEY")
    if not key:
        return "S2_API_KEY is not set in this server's environment."
    fields = "title,year,venue,authors,externalIds,openAccessPdf"
    url = ("https://api.semanticscholar.org/graph/v1/paper/search"
           f"?query={urllib.parse.quote(query)}&fields={fields}"
           f"&limit={limit}")
    papers = _get(url, {"x-api-key": key}).get("data", [])
    if not papers:
        return "No results."
    lines = []
    for paper in papers:
        authors = ", ".join(a["name"] for a in paper.get("authors", [])[:6])
        doi = (paper.get("externalIds") or {}).get("DOI", "")
        pdf = (paper.get("openAccessPdf") or {}).get("url", "")
        lines.append(f"- {paper.get('title', '?')} "
                     f"({paper.get('year', '?')})")
        lines.append(f"    {authors}")
        detail = f"    {paper.get('venue') or 'venue unknown'}"
        if doi:
            detail += f" | doi:{doi}"
        lines.append(detail)
        if pdf:
            lines.append(f"    open access: {pdf}")
    return "\n".join(lines)


def scopus(query, limit):
    key = os.environ.get("SCOPUS_API_KEY")
    if not key:
        return "SCOPUS_API_KEY is not set in this server's environment."
    encoded = urllib.parse.quote(f"TITLE-ABS-KEY({query})")
    url = ("https://api.elsevier.com/content/search/scopus"
           f"?query={encoded}&count={limit}")
    results = _get(url, {"X-ELS-APIKey": key,
                         "Accept": "application/json"})["search-results"]
    entries = results.get("entry", [])
    if not entries or "error" in entries[0]:
        return "No results."
    lines = [f"({results.get('opensearch:totalResults', '?')} total "
             "Scopus matches)"]
    for entry in entries:
        year = (entry.get("prism:coverDate") or "?")[:4]
        lines.append(f"- {entry.get('dc:title', '?')} ({year})")
        detail = (f"    {entry.get('dc:creator', '?')} | "
                  f"{entry.get('prism:publicationName', 'venue unknown')}")
        if entry.get("prism:volume"):
            detail += (f" {entry['prism:volume']}"
                       f"({entry.get('prism:issueIdentifier', '-')})"
                       f":{entry.get('prism:pageRange', '?')}")
        lines.append(detail)
        if entry.get("prism:doi"):
            lines.append(f"    doi:{entry['prism:doi']}")
    return "\n".join(lines)


def handle_call(name, arguments):
    query = arguments.get("query", "").strip()
    limit = int(arguments.get("limit", 5))
    if not query:
        return "Empty query."
    try:
        if name == "search_semantic_scholar":
            return semantic_scholar(query, limit)
        if name == "search_scopus":
            return scopus(query, limit)
    except urllib.error.HTTPError as error:
        return f"API error: HTTP {error.code} ({error.reason})."
    except urllib.error.URLError as error:
        return f"Network error: {error.reason}."
    return f"Unknown tool: {name}"


def respond(request_id, result):
    print(json.dumps({"jsonrpc": "2.0", "id": request_id,
                      "result": result}), flush=True)


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = message.get("method")
        request_id = message.get("id")
        if method == "initialize":
            respond(request_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "scholar", "version": "1.0.0"},
            })
        elif method == "tools/list":
            respond(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = message.get("params", {})
            text = handle_call(params.get("name", ""),
                               params.get("arguments", {}))
            respond(request_id,
                    {"content": [{"type": "text", "text": text}]})
        elif request_id is not None:  # unknown request: empty result
            respond(request_id, {})
        # notifications (no id) are consumed silently


if __name__ == "__main__":
    main()
