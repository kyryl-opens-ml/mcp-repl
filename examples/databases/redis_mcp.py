# redis_mcp.py
# Requires: pip install mcp redis
import os
import redis
from mcp.server.fastmcp import FastMCP

# Redis connection configuration (hardcoded)
REDIS_URL = "redis://default:oxHEJDLngOmEVUfVfTkBuFjzUeADzrvw@tramway.proxy.rlwy.net:26584"
REDIS_HOST = "tramway.proxy.rlwy.net"
REDIS_PORT = 26584
REDIS_DB = 0  # Default database
REDIS_PASSWORD = "oxHEJDLngOmEVUfVfTkBuFjzUeADzrvw"

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

# Initialize the MCP server
mcp = FastMCP("Redis", dependencies=["redis"])

@mcp.tool()
def set_value(key: str, value: str) -> str:
    """Set the given key to the specified value in Redis."""
    redis_client.set(key, value)
    return f"OK (set {key})"

@mcp.tool()
def get_value(key: str) -> str:
    """Get the value of the specified key from Redis. Returns None if the key doesn't exist."""
    val = redis_client.get(key)
    if val is None:
        return None
    # Decode bytes to string for return
    return val.decode("utf-8")

@mcp.tool()
def list_keys(pattern: str = "*") -> list:
    """List all keys matching the given pattern (glob style)."""
    keys = redis_client.keys(pattern)
    # Decode bytes keys to strings
    return [key.decode("utf-8") for key in keys]

@mcp.tool()
def delete_key(key: str) -> int:
    """Delete the specified key from Redis. Returns the number of keys deleted (0 or 1)."""
    return redis_client.delete(key)

if __name__ == "__main__":
    mcp.run()