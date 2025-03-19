import redis
from mcp.server.fastmcp import FastMCP

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = "redis"

redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD
)

mcp = FastMCP(
    "Redis",
    instructions="You are a Redis database manager. You can set, get, and list keys in Redis.",
)


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
    return val.decode("utf-8")


@mcp.tool()
def list_keys(pattern: str = "*") -> list:
    """List all keys matching the given pattern (glob style)."""
    keys = redis_client.keys(pattern)
    return [key.decode("utf-8") for key in keys]


@mcp.tool()
def delete_key(key: str) -> int:
    """Delete the specified key from Redis. Returns the number of keys deleted (0 or 1)."""
    return redis_client.delete(key)


if __name__ == "__main__":
    mcp.run()
