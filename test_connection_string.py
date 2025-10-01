#!/usr/bin/env python3
"""
Test connection string generation
"""
from urllib.parse import quote_plus

# Test data
NEO4J_URI = "neo4j+s://a616c3d7.databases.neo4j.io"
NEO4J_USER = "a616c3d7"
NEO4J_PASSWORD = "YK8MxjSmRVELhUxf7a8KRVw_g_NTRiQGbWQMUr1Bsi0"

print(f"Original URI: {NEO4J_URI}")
print(f"User: {NEO4J_USER}")

# Encode password
encoded_password = quote_plus(NEO4J_PASSWORD)
print(f"Encoded password: {encoded_password}")

# Test the logic
if "@" in NEO4J_URI:
    print("URI already contains @")
    DATABASE_URL = NEO4J_URI
else:
    print("URI does not contain @, adding credentials...")
    if NEO4J_URI.startswith("neo4j+s://"):
        DATABASE_URL = NEO4J_URI.replace("neo4j+s://", f"neo4j+s://{NEO4J_USER}:{encoded_password}@")
        print(f"Used neo4j+s:// replacement")
    else:
        print("No matching protocol found")

print(f"Final DATABASE_URL: {DATABASE_URL}")

# Test with neomodel
try:
    from neomodel import config, db
    config.DATABASE_URL = DATABASE_URL
    print(f"Set neomodel DATABASE_URL: {config.DATABASE_URL}")
    
    # Test connection
    result = db.cypher_query("RETURN 1")
    print("✅ Connection successful!")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
