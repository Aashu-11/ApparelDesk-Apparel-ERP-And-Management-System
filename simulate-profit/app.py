"""
Profit Simulation - FastAPI Web Application
============================================

A beautiful web interface for the ApparelDesk High-Precision Profit Simulation Engine.
Integrates with prog.py to provide real-time profit calculations with an elegant UI.

Color Scheme: Eggshell White (#F0EAD6) & Dark Emerald (#022D1E)
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Import the simulation logic from prog.py
from prog import (
    SimulationRequest,
    SimulationResponse,
    simulate_profit,
    get_db_connection,
    ProductRepository,
    DiscountRepository,
    PaymentTermRepository,
    ProfitCalculator,
    ProfitAdvisor,
    ScenarioAnalyzer
)

# Load environment variables
load_dotenv()

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Profit Simulation",
    description="High-precision financial simulation with intelligent advisory",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Serve the main web interface."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Profit Simulation Engine",
        "version": "1.0.0",
        "app_name": os.getenv("APP_NAME", "Profit Simulation")
    }


@app.post("/api/simulate-profit", response_model=SimulationResponse)
async def api_simulate_profit(request: SimulationRequest):
    """
    API endpoint for profit simulation.
    Delegates to the simulate_profit function from prog.py
    """
    return await simulate_profit(request)


@app.get("/api/config")
async def get_config():
    """Get application configuration (colors, branding)."""
    return {
        "app_name": os.getenv("APP_NAME", "Profit Simulation"),
        "primary_color": os.getenv("PRIMARY_COLOR", "#022D1E"),
        "secondary_color": os.getenv("SECONDARY_COLOR", "#F0EAD6"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║                  PROFIT SIMULATION ENGINE                      ║
    ║                                                                ║
    ║  🚀 Server starting on http://localhost:{port}                  ║
    ║  📊 Beautiful UI with Dark Emerald & Eggshell White theme      ║
    ║  💰 High-precision financial calculations                      ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=port)
