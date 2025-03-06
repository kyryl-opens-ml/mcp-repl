# postgresql_mcp.py
# Requires: pip install mcp psycopg2-binary
import os
import psycopg2
from psycopg2 import sql
from mcp.server.fastmcp import FastMCP

# Database connection configuration (hardcoded)
PG_HOST = "turntable.proxy.rlwy.net"
PG_PORT = "17677"
PG_USER = "postgres"
PG_PASSWORD = "JEQmdfxkGIwQpInLrqxDTXsIEwXLdzjG"
PG_DATABASE = "railway"

# Establish a connection to PostgreSQL
conn = psycopg2.connect(
    host=PG_HOST, port=PG_PORT,
    user=PG_USER, password=PG_PASSWORD,
    dbname=PG_DATABASE
)
conn.autocommit = False  # Use manual commit control

# Initialize the MCP server
mcp = FastMCP("PostgreSQL", dependencies=["psycopg2-binary"])

@mcp.tool()
def execute_query(query: str) -> str:
    """Execute an arbitrary SQL query. Returns results for SELECT, or a success message for others."""
    cur = conn.cursor()
    cur.execute(query)
    # If it's a SELECT or similar, fetch results
    command = query.strip().split()[0].lower()
    if command == "select" or command == "show" or command == "describe":
        rows = cur.fetchall()
        # Convert result rows to string for display
        return str(rows)
    else:
        # For INSERT/UPDATE/DELETE/DDL, commit the transaction
        conn.commit()
        return "Query executed successfully."

@mcp.tool()
def create_table(name: str, schema: str) -> str:
    """Create a new table with the given name and schema (column definitions)."""
    cur = conn.cursor()
    cur.execute(sql.SQL("CREATE TABLE {} ({})").format(
        sql.Identifier(name),
        sql.SQL(schema)
    ))
    conn.commit()
    return f"Table '{name}' created."

@mcp.tool()
def insert_data(table: str, data: dict) -> str:
    """Insert a row of data into the specified table. `data` is a dict of column values."""
    cur = conn.cursor()
    # Build columns and values for insertion
    columns = [sql.Identifier(col) for col in data.keys()]
    values = [sql.Literal(val) for val in data.values()]
    insert_stmt = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(columns),
        sql.SQL(", ").join(values)
    )
    cur.execute(insert_stmt)
    conn.commit()
    return f"Data inserted into table '{table}'."

@mcp.tool()
def fetch_data(query: str) -> str:
    """Fetch data by executing a SELECT query and returning the results."""
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    return str(rows)

if __name__ == "__main__":
    mcp.run()