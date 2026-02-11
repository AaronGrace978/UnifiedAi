"""
Run UnifiedAi backend server
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=10000,  # UnifiedAi port
        reload=False  # Disabled to prevent crash on Windows
    )

