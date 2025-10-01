import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from neomodel import config

# Load .env file (only in development)
if os.path.exists(os.path.join(os.path.dirname(__file__), ".env")):
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_URI = os.getenv("NEO4J_URI")

if not all([NEO4J_USER, NEO4J_PASSWORD, NEO4J_URI]):
    raise ValueError("❌ Missing Neo4j environment variables. Please set NEO4J_USER, NEO4J_PASSWORD, and NEO4J_URI")

# Encode password for URL
encoded_password = quote_plus(NEO4J_PASSWORD)

# Build connection URL
# Handle both local development and production URLs
if "@" in NEO4J_URI:
    # Production URL already contains credentials
    config.DATABASE_URL = NEO4J_URI
else:
    # Local development - add credentials to URL
    if NEO4J_URI.startswith("bolt://"):
        config.DATABASE_URL = NEO4J_URI.replace("bolt://", f"bolt://{NEO4J_USER}:{encoded_password}@")
    elif NEO4J_URI.startswith("neo4j://"):
        config.DATABASE_URL = NEO4J_URI.replace("neo4j://", f"neo4j://{NEO4J_USER}:{encoded_password}@")
    elif NEO4J_URI.startswith("neo4j+s://"):
        config.DATABASE_URL = NEO4J_URI.replace("neo4j+s://", f"neo4j+s://{NEO4J_USER}:{encoded_password}@")
    elif NEO4J_URI.startswith("neo4j+ssc://"):
        config.DATABASE_URL = NEO4J_URI.replace("neo4j+ssc://", f"neo4j+ssc://{NEO4J_USER}:{encoded_password}@")
    else:
        config.DATABASE_URL = f"bolt://{NEO4J_USER}:{encoded_password}@{NEO4J_URI}"

print("[ℹ️] Connecting to Neo4j...")
# Don't print the full URL in production to avoid exposing credentials
if "localhost" in config.DATABASE_URL:
    print(f"[ℹ️] Local Neo4j connection: {config.DATABASE_URL}")
else:
    # Show connection details without password for debugging
    protocol = config.DATABASE_URL.split("://")[0] if "://" in config.DATABASE_URL else "unknown"
    host_part = config.DATABASE_URL.split("@")[-1] if "@" in config.DATABASE_URL else "unknown"
    print(f"[ℹ️] Production Neo4j connection: {protocol}://*****@{host_part}")
