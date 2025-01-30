from fastapi import FastAPI
from .routers import reddit

app = FastAPI(
    title="Social Listener",
    description="Social media monitoring tool",
    version="1.0.0"
)

# Include routers
app.include_router(reddit.router)

@app.get("/")
async def root():
    return {"status": "running"}
