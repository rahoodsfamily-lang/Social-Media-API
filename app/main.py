from fastapi import FastAPI
from app.config import config  # <-- make sure this is imported first
from neomodel import db
from neo4j.exceptions import AuthError, ServiceUnavailable
from app.routers import person, users, posts, comments, groups
from datetime import datetime

app = FastAPI(
    title="Social Media API",
    description="A comprehensive social media platform built with FastAPI and Neo4j",
    version="1.0.0"
)

# Include all routers
app.include_router(person.router)  # Keep existing router
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(groups.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Social Media API",
        "description": "A comprehensive social media platform built with FastAPI and Neo4j",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db.cypher_query("RETURN 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.on_event("startup")
def startup_db_check():
    try:
        db.cypher_query("RETURN 1")
        print("[✅] Neo4j connection successful!")
    except AuthError:
        print("[❌] Authentication failed: Check username/password.")
        raise
    except ServiceUnavailable:
        print("[❌] Cannot connect: Is Neo4j running?")
        raise
    except Exception as e:
        print(f"[❌] Neo4j connection failed: {e}")
        raise
