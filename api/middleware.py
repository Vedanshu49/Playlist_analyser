from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Response
import time
from typing import Dict, Optional

class CacheControlMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, cache_time: int = 3600):
        super().__init__(app)
        self.cache_time = cache_time
        
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Don't cache if it's not a GET request or if it's an error response
        if request.method != "GET" or response.status_code >= 400:
            return response
            
        # Don't cache authenticated endpoints
        if request.session.get('token_info'):
            return response
            
        # Add cache control headers for public endpoints
        response.headers["Cache-Control"] = f"public, max-age={self.cache_time}"
        return response

class ResponseTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000)
        response.headers["X-Process-Time"] = str(process_time) + "ms"
        return response
