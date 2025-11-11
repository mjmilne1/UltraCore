"""
UltraCore API Server

Simple script to run the FastAPI server
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting UltraCore Banking Platform API...")
    print("=" * 70)
    print()
    print("📍 API will be available at:")
    print("   • Main: http://localhost:8000")
    print("   • Docs: http://localhost:8000/api/v1/docs")
    print("   • Health: http://localhost:8000/api/v1/health")
    print()
    print("Press CTRL+C to stop")
    print()
    
    uvicorn.run(
        "ultracore.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
