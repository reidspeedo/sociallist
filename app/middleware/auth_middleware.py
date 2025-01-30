from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger('uvicorn')

security = HTTPBasic()

class BasicAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, username: str, password: str):
        super().__init__(app)
        self.username = username
        self.password = password
        # Define paths that don't require authentication
        self.public_paths = []

    async def dispatch(self, request: Request, call_next):
        # Check if the path starts with any of the public paths
        if any(request.url.path.startswith(path) for path in self.public_paths):
            return await call_next(request)

        try:
            credentials: HTTPBasicCredentials = await security(request)
            if credentials.username != self.username or credentials.password != self.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Basic"},
                )
        except HTTPException as e:
            logger.error(f"Authentication failed: {e.detail}")
            return Response(
                content="Unauthorized access. Please check your credentials.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Basic"},
            )
        
        response = await call_next(request)
        return response 