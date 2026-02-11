"""
UnifiedAi - Main FastAPI Application
The Ultimate Meta-Intelligence Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import traceback
import os

from app.config import settings
from app.database import engine, Base

# Import API routers with error handling
try:
    from app.api import meta, tech, brain
    print("[OK] Loaded: meta, tech, brain")
except Exception as e:
    print(f"[ERROR] Error loading meta/tech/brain: {e}")
    raise

try:
    from app.api import agent
    print("[OK] Loaded: agent (matrix-style orchestration)")
except Exception as e:
    print(f"[ERROR] Error loading agent module: {e}")
    from fastapi import APIRouter
    agent = type('agent', (), {'router': APIRouter()})()

try:
    from app.api import insights
    print("[OK] Loaded: insights")
except Exception as e:
    print(f"[ERROR] Error loading insights module: {e}")
    import traceback
    traceback.print_exc()
    # Create a dummy router so the app doesn't crash
    from fastapi import APIRouter
    insights = type('insights', (), {'router': APIRouter()})()

try:
    from app.api import activateprime
    print("[OK] Loaded: activateprime (emotional intelligence)")
except Exception as e:
    print(f"[ERROR] Error loading activateprime module: {e}")
    import traceback
    traceback.print_exc()
    from fastapi import APIRouter
    activateprime = type('activateprime', (), {'router': APIRouter()})()

try:
    from app.api import search
    print("[OK] Loaded: search (semantic search)")
except Exception as e:
    print(f"[ERROR] Error loading search module: {e}")
    import traceback
    traceback.print_exc()
    from fastapi import APIRouter
    search = type('search', (), {'router': APIRouter()})()

try:
    from app.api import proposals
    print("[OK] Loaded: proposals (research proposals)")
except Exception as e:
    print(f"[ERROR] Error loading proposals module: {e}")
    import traceback
    traceback.print_exc()
    from fastapi import APIRouter
    proposals = type('proposals', (), {'router': APIRouter()})()

try:
    from app.api import ensemble
    print("[OK] Loaded: ensemble (multi-model thinking)")
except Exception as e:
    print(f"[ERROR] Error loading ensemble module: {e}")
    import traceback
    traceback.print_exc()
    from fastapi import APIRouter
    ensemble = type('ensemble', (), {'router': APIRouter()})()

try:
    from app.api import graph
    print("[OK] Loaded: graph (graph algorithms)")
except Exception as e:
    print(f"[ERROR] Error loading graph module: {e}")
    import traceback
    traceback.print_exc()
    from fastapi import APIRouter
    graph = type('graph', (), {'router': APIRouter()})()

try:
    from app.api import physics
    print("[OK] Loaded: physics (physics simulation)")
except Exception as e:
    print(f"[ERROR] Error loading physics module: {e}")
    import traceback
    traceback.print_exc()
    from fastapi import APIRouter
    physics = type('physics', (), {'router': APIRouter()})()

try:
    from app.api import voice
    print("[OK] Loaded: voice (voice interface)")
except Exception as e:
    print(f"[ERROR] Error loading voice module: {e}")
    from fastapi import APIRouter
    voice = type('voice', (), {'router': APIRouter()})()

try:
    from app.api import export
    print("[OK] Loaded: export (enhanced export)")
except Exception as e:
    print(f"[ERROR] Error loading export module: {e}")
    from fastapi import APIRouter
    export = type('export', (), {'router': APIRouter()})()

try:
    from app.api import discovery
    print("[OK] Loaded: discovery (auto-discovery)")
except Exception as e:
    print(f"[ERROR] Error loading discovery module: {e}")
    from fastapi import APIRouter
    discovery = type('discovery', (), {'router': APIRouter()})()

try:
    from app.api import ar
    print("[OK] Loaded: ar (AR/holographic)")
except Exception as e:
    print(f"[ERROR] Error loading ar module: {e}")
    from fastapi import APIRouter
    ar = type('ar', (), {'router': APIRouter()})()

try:
    from app.api import collaboration
    print("[OK] Loaded: collaboration (multi-user)")
except Exception as e:
    print(f"[ERROR] Error loading collaboration module: {e}")
    from fastapi import APIRouter
    collaboration = type('collaboration', (), {'router': APIRouter()})()

try:
    from app.api import knowledge
    print("[OK] Loaded: knowledge (external knowledge)")
except Exception as e:
    print(f"[ERROR] Error loading knowledge module: {e}")
    from fastapi import APIRouter
    knowledge = type('knowledge', (), {'router': APIRouter()})()

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="The Ultimate Meta-Intelligence Platform - Unifying all SUPERSECRETS"
)

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using *
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(meta.router, prefix="/api/meta", tags=["Meta-Intelligence"])
app.include_router(tech.router, prefix="/api/tech", tags=["Breakthrough Technologies"])
app.include_router(brain.router, prefix="/api/brain", tags=["Brain Thinker"])
app.include_router(agent.router)

# Include insights router with error handling
try:
    app.include_router(insights.router, prefix="/api/insights", tags=["Insights & Knowledge Graph"])
    print("[OK] Registered insights router at /api/insights")
except Exception as e:
    print(f"[ERROR] Error registering insights router: {e}")
    import traceback
    traceback.print_exc()

# Include ActivatePrime router
try:
    app.include_router(activateprime.router, tags=["ActivatePrime - Emotional Intelligence"])
    print("[OK] Registered activateprime router at /api/activateprime")
except Exception as e:
    print(f"[ERROR] Error registering activateprime router: {e}")
    import traceback
    traceback.print_exc()

# Include Semantic Search router
try:
    app.include_router(search.router, tags=["Semantic Search"])
    print("[OK] Registered search router at /api/search")
except Exception as e:
    print(f"[ERROR] Error registering search router: {e}")
    import traceback
    traceback.print_exc()

# Include Research Proposals router
try:
    app.include_router(proposals.router, tags=["Research Proposals"])
    print("[OK] Registered proposals router at /api/proposals")
except Exception as e:
    print(f"[ERROR] Error registering proposals router: {e}")
    import traceback
    traceback.print_exc()

# Include Ensemble Thinking router
try:
    app.include_router(ensemble.router, tags=["Ensemble Thinking"])
    print("[OK] Registered ensemble router at /api/ensemble")
except Exception as e:
    print(f"[ERROR] Error registering ensemble router: {e}")
    import traceback
    traceback.print_exc()

# Include Graph Analysis router
try:
    app.include_router(graph.router, tags=["Graph Analysis"])
    print("[OK] Registered graph router at /api/graph")
except Exception as e:
    print(f"[ERROR] Error registering graph router: {e}")
    import traceback
    traceback.print_exc()

# Include Physics Simulation router
try:
    app.include_router(physics.router, tags=["Physics Simulation"])
    print("[OK] Registered physics router at /api/physics")
except Exception as e:
    print(f"[ERROR] Error registering physics router: {e}")
    import traceback
    traceback.print_exc()

# Include Voice Interface router
try:
    app.include_router(voice.router, tags=["Voice Interface"])
    print("[OK] Registered voice router at /api/voice")
except Exception as e:
    print(f"[ERROR] Error registering voice router: {e}")

# Include Export router
try:
    app.include_router(export.router, tags=["Export"])
    print("[OK] Registered export router at /api/export")
except Exception as e:
    print(f"[ERROR] Error registering export router: {e}")

# Include Auto-Discovery router
try:
    app.include_router(discovery.router, tags=["Auto-Discovery"])
    print("[OK] Registered discovery router at /api/discovery")
except Exception as e:
    print(f"[ERROR] Error registering discovery router: {e}")

# Include AR/Holographic router
try:
    app.include_router(ar.router, tags=["AR/Holographic"])
    print("[OK] Registered ar router at /api/ar")
except Exception as e:
    print(f"[ERROR] Error registering ar router: {e}")

# Include Collaboration router
try:
    app.include_router(collaboration.router, tags=["Collaboration"])
    print("[OK] Registered collaboration router at /api/collaboration")
except Exception as e:
    print(f"[ERROR] Error registering collaboration router: {e}")

# Include External Knowledge router
try:
    app.include_router(knowledge.router, tags=["External Knowledge"])
    print("[OK] Registered knowledge router at /api/knowledge")
except Exception as e:
    print(f"[ERROR] Error registering knowledge router: {e}")

# Serve frontend static files
# __file__ is at: backend/app/main.py
# Go up 2 levels to get to UnifiedAi root, then add frontend
_backend_dir = os.path.dirname(os.path.dirname(__file__))  # backend/
_project_root = os.path.dirname(_backend_dir)  # UnifiedAi/
FRONTEND_DIR = os.path.join(_project_root, "frontend")
print(f"[INFO] Backend dir: {_backend_dir}")
print(f"[INFO] Project root: {_project_root}")
print(f"[INFO] Frontend directory: {FRONTEND_DIR}")
print(f"[INFO] Frontend directory exists: {os.path.exists(FRONTEND_DIR)}")

if os.path.exists(FRONTEND_DIR):
    # Mount at root to serve CSS/JS without /static prefix
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    
    # Serve idle.html - CRITICAL: must be before catch-all route
    @app.get("/idle.html")
    async def serve_idle():
        idle_path = os.path.join(FRONTEND_DIR, "idle.html")
        print(f"[DEBUG] Serving /idle.html from: {idle_path}")
        if os.path.exists(idle_path):
            return FileResponse(idle_path, media_type="text/html")
        print(f"[ERROR] idle.html not found at: {idle_path}")
        return JSONResponse(status_code=404, content={"detail": "Lock screen not found"})
    
    # Serve index.html
    @app.get("/index.html")
    async def serve_index():
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")
        return JSONResponse(status_code=404, content={"detail": "Index page not found"})
    
    # Also serve individual frontend files at root level for direct access
    @app.get("/styles.css")
    async def serve_styles():
        return FileResponse(os.path.join(FRONTEND_DIR, "styles.css"))
    
    @app.get("/app.js")
    async def serve_app():
        return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))
    
    @app.get("/effects.js")
    async def serve_effects():
        return FileResponse(os.path.join(FRONTEND_DIR, "effects.js"))
    
    @app.get("/insights.js")
    async def serve_insights():
        return FileResponse(os.path.join(FRONTEND_DIR, "insights.js"))

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    print(f"ERROR: {str(exc)}")
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

@app.get("/")
async def root():
    """Serve the frontend"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {
        "message": "UnifiedAi - The Ultimate Meta-Intelligence Platform",
        "version": settings.APP_VERSION,
        "status": "running",
        "frontend": "http://localhost:10000/static/index.html"
    }

@app.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "message": "UnifiedAi - The Ultimate Meta-Intelligence Platform",
        "version": settings.APP_VERSION,
        "status": "running",
        "features": [
            "Meta-Intelligence Orchestrator",
            "Breakthrough Technology Designer",
            "Physics Simulation Engine",
            "ActivatePrime Emotional Intelligence",
            "Echo Archaeology (Emotion Detection)",
            "Glyph Logic (Symbolic Language)",
            "SoulFrame (Personality Sync)",
            "Semantic Search with Vector Embeddings",
            "Research Proposal Generator",
            "Multi-Model Ensemble Thinking",
            "Advanced Knowledge Graph Algorithms",
            "Voice Interface (TTS/STT)",
            "Enhanced Export (PNG/PDF)",
            "Auto-Discovery Dream Mode",
            "AR/Holographic Interface",
            "Multi-User Collaboration",
            "External Knowledge Integration (arXiv/Wikipedia)"
        ]
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "platform": "UnifiedAi"}

# Catch-all route for frontend navigation (must be last)
# This handles any other frontend files that aren't explicitly defined above
@app.get("/{path:path}")
async def catch_all(path: str):
    """Catch-all route for frontend files"""
    # Don't catch API routes, health, root, or explicitly defined routes
    if (path.startswith("api/") or path == "health" or path == "" or 
        path in ["idle.html", "index.html", "styles.css", "app.js", "effects.js", "insights.js"]):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    
    # Try to serve other frontend files
    if os.path.exists(FRONTEND_DIR):
        file_path = os.path.join(FRONTEND_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Determine content type
            if path.endswith('.html'):
                return FileResponse(file_path, media_type="text/html")
            elif path.endswith('.css'):
                return FileResponse(file_path, media_type="text/css")
            elif path.endswith('.js'):
                return FileResponse(file_path, media_type="application/javascript")
            else:
                return FileResponse(file_path)
    
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.BACKEND_PORT)

