import uvicorn
import os
import multiprocessing

if __name__ == "__main__":
    # Get configuration from environment
    port = int(os.getenv("PYTHON_PORT", 8003))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Determine workers count
    # For stateful SSE (Server-Sent Events) with in-memory session storage,
    # we MUST use a single worker unless we implement sticky sessions or 
    # a shared backend (like Redis) for stream state.
    # Current architecture relies on `sessions` dict in app.py.
    workers = 1 
    
    print(f"Starting production server on {host}:{port} with {workers} workers")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
