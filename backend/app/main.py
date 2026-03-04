# Import main class for web application creation
from fastapi import FastAPI 
# Import router from app/api/releases.py 
from app.api.releases import router as releases_router

# Create an app-object
app = FastAPI()
# Connect earlier added router to get releases
app.include_router(releases_router, prefix="/api")

# Root address. Useful for health and availability checks (monitoring)
@app.get("/")
def root():
	return {"status": "ok", "message": "Metal Intel backend is running"}

'''
TBA:
--- Lifespan (Startup / Shutdown) - check connection with the database on startup
--- Middleware (CORS) - in case of frontend on another port / domain in future
--- Error handler - correct error handler for structured logging
'''