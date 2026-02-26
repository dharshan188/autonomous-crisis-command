import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager

from ai_model import CrisisModel
from crisis_engine import CrisisEngine
from services.audit import get_audit_log


# Request/Response models
class CrisisCommandRequest(BaseModel):
    """Request model for crisis command endpoint"""
    crises: list
    approved: bool


class CrisisCommandResponse(BaseModel):
    """Response model for crisis command endpoint"""
    status: str
    details: dict | list | None = None
    execution_result: dict | None = None
    alerts: list | None = None


# Global variables for model and engine
crisis_model: CrisisModel | None = None
crisis_engine: CrisisEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage startup and shutdown of the application.
    Initializes the CrisisModel and CrisisEngine once at startup.
    """
    global crisis_model, crisis_engine
    
    # Startup
    print("Initializing CrisisModel...")
    crisis_model = CrisisModel()
    
    print("Initializing CrisisEngine...")
    crisis_engine = CrisisEngine(crisis_model)
    
    print("Application startup complete")
    
    yield
    
    # Shutdown
    print("Shutting down application...")


# Create FastAPI app with lifespan context
app = FastAPI(
    title="Autonomous Crisis Command System",
    description="AI-powered crisis detection and response system",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/crisis_command", response_model=CrisisCommandResponse)
async def crisis_command(request: CrisisCommandRequest):
    """
    Process crisis reports and execute appropriate response actions.
    
    Args:
        request: CrisisCommandRequest containing:
            - crises: List of crisis text descriptions
            - approved: Boolean indicating if high-risk actions are pre-approved
    
    Returns:
        CrisisCommandResponse with processing results and status
    """
    if crisis_engine is None:
        return {
            "status": "ERROR",
            "details": "Crisis engine not initialized"
        }
    
    # Process the crises through the engine
    result = crisis_engine.process_crises(request.crises, request.approved)
    
    # Format response based on the result
    if result["status"] == "PENDING_APPROVAL":
        return {
            "status": result["status"],
            "details": result["details"]
        }
    else:  # EXECUTED status
        return {
            "status": result["status"],
            "execution_result": result["execution_result"],
            "alerts": result["alerts"]
        }


@app.get("/audit")
async def get_audit():
    """
    Retrieve the complete audit log of all crisis command operations.
    
    Returns:
        List of audit log entries with timestamps, event types, and data
    """
    return get_audit_log()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_initialized": crisis_model is not None,
        "engine_initialized": crisis_engine is not None
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
