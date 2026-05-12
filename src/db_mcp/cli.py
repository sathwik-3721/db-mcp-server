import argparse
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse

from src.db_mcp.server import mcp
from src.db_mcp.core.logger import setup_logger
from src.db_mcp.core.db import db_manager

logger = setup_logger(__name__)

async def health_check(request):
    """Simple liveness probe."""
    return JSONResponse({"status": "healthy"})

async def ready_check(request):
    """Readiness probe testing DB connectivity."""
    status = db_manager.check_connection()
    status_code = 200 if status.get("status") == "healthy" else 503
    return JSONResponse(status, status_code=status_code)

def create_app():
    """Create a Starlette app that combines health endpoints with the MCP server."""
    # Get the built-in Streamable HTTP app from FastMCP
    # This already handles POST /mcp (which is what Google ADK agents use)
    mcp_app = mcp.streamable_http_app()
    
    # Add our custom health/ready routes to the MCP app
    mcp_app.add_route("/health", health_check, methods=["GET"])
    mcp_app.add_route("/ready", ready_check, methods=["GET"])
    
    return mcp_app


def main():
    parser = argparse.ArgumentParser(description="Database Agnostic MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["stdio", "sse", "http"], 
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--bind", 
        type=str, 
        default="127.0.0.1:8080",
        help="Bind address and port (default: 127.0.0.1:8080)"
    )
    
    args = parser.parse_args()
    
    if args.transport in ["sse", "http"]:
        try:
            host, port = args.bind.split(":")
            port = int(port)
        except ValueError:
            logger.error("Invalid bind address. Use format HOST:PORT (e.g. 127.0.0.1:8080)")
            exit(1)
            
        logger.info(f"Starting MCP Server on HTTP/SSE transport at http://{host}:{port}/mcp")
        app = create_app()
        
        # Suppress harmless Windows ProactorEventLoop ConnectionResetError (WinError 10054)
        # This occurs when the HTTP client closes the connection after receiving its response.
        import logging as _logging
        _logging.getLogger("asyncio").setLevel(_logging.CRITICAL)
        
        uvicorn.run(app, host=host, port=port)
    else:
        # stdio transport
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
