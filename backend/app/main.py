import asyncio
from fastapi import FastAPI
from app.api import releases
from app.db import init_pool

app = FastAPI()
app.include_router(releases.router, prefix="/api")

@app.on_event("startup")
async def startup():
    await init_pool()