from fastapi import FastAPI
from .routers import reddit
from .middleware.auth_middleware import BasicAuthMiddleware
from .config.settings import get_settings

app = FastAPI(
    title="Social Listener",
    description="Social media monitoring tool",
    version="1.0.0"
)

# Retrieve settings
settings = get_settings()

# Add middleware
app.add_middleware(
    BasicAuthMiddleware,
    username=settings.API_USERNAME,
    password=settings.API_PASSWORD
)

# Include routers
app.include_router(reddit.router)

@app.get("/")
async def root():
    return {"status": "running"}
