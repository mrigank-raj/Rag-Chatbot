"""
Main FastAPI application entrypoint.
Sets up CORS, registers routes, and exposes the app instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

# Create the FastAPI application instance
app = FastAPI(
    title="HDFC Mutual Fund FAQ Assistant API",
    description="RAG-powered API for factual answers regarding 5 specific HDFC mutual funds.",
    version="1.0.0",
)

# Configure Cross-Origin Resource Sharing (CORS)
# Allows the React frontend (which will run on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the specific frontend domain
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Register the routes under the /api prefix
app.include_router(router, prefix="/api")


# Optional root endpoint just to verify the server is up
@app.get("/")
async def root():
    return {"message": "Welcome to the HDFC MF FAQ API. Visit /docs for the interactive API documentation."}


if __name__ == "__main__":
    import uvicorn
    # Run the server locally on port 8000 when the script is executed directly
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
