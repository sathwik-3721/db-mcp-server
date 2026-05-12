import argparse
from src.server import mcp

def main():
    parser = argparse.ArgumentParser(description="Database Agnostic MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse"], 
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to use for SSE transport (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.transport == "sse":
        print(f"Starting MCP Server on SSE transport (Port {args.port})...")
        mcp.run(transport="sse", port=args.port)
    else:
        # For stdio, logging should be minimal to avoid corrupting the JSON-RPC stream
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
