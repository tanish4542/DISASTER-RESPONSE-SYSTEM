"""
Disaster Response System Backend
FastAPI application entry point

Initializes:
- Database (SQLite)
- CORS middleware
- Emergency API routes
- Health check endpoints
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes.emergency import router as emergency_router

# Initialize database
init_db()

# Create FastAPI application
app = FastAPI(
    title="Disaster Response System API",
    description="Backend API for coordinating emergency response and rescue operations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:4173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(emergency_router)


@app.get("/")
async def root():
    """Root health check endpoint."""
    return JSONResponse({
        "status": "ok",
        "service": "Disaster Response System Backend",
        "version": "1.0.0",
        "message": "Backend is running successfully",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "Disaster Response System API",
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
