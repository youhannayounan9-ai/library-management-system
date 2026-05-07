import time
import logging
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """Logs HTTP method, path, status code, and response time for every request."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {process_time:.4f}s"
    )
    
    # Optional: Add processing time to response headers
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response