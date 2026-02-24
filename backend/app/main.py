from fastapi import FastAPI
from app.api.releases import router as releases_router

app = FastAPI()

app.include_router(releases_router, prefix="/api")

@app.get("/")
def root():
	return {"status": "ok", "message": "Metal Intel backend is running"}
