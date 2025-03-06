# mysql_mcp.py
# Requires: pip install mcp mysql-connector-python
import os
import mysql.connector
from mysql.connector import Error
from mcp.server.fastmcp import FastMCP

# Database connection configuration (hardcoded)
MYSQL_HOST = "monorail.proxy.rlwy.net"
MYSQL_PORT = "45371"
MYSQL_USER = "root"
MYSQL_PASSWORD = "hGCf3-GHcBcbDFGhcCHGEcfcbcFGBdAh"
MYSQL_DATABASE = "railway"

# Establish a connection to MySQL
conn = mysql.connector.connect(
    host=MYSQL_HOST, port=MYSQL_PORT,
    user=MYSQL_USER, password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)
conn.autocommit = False  # Use manual commit control

# Initialize the MCP server
mcp = FastMCP("MySQL", dependencies=["mysql-connector-python"])

@mcp.tool()
def execute_query(query: str) -> str:
    """Execute an arbitrary SQL query. Returns results for SELECT, or a success message for others."""
    cursor = conn.cursor()
    cursor.execute(query)
    # If it's a SELECT or similar, fetch results
    command = query.strip().split()[0].lower()
    if command == "select" or command == "show" or command == "describe":
        rows = cursor.fetchall()
        # Convert result rows to string for display
        return str(rows)
    else:
        # For INSERT/UPDATE/DELETE/DDL, commit the transaction
        conn.commit()
        return f"Query executed successfully. Rows affected: {cursor.rowcount}"

@mcp.tool()
def create_table(name: str, schema: str) -> str:
    """Create a new table with the given name and schema (column definitions)."""
    cursor = conn.cursor()
    query = f"CREATE TABLE {name} ({schema})"
    cursor.execute(query)
    conn.commit()
    return f"Table '{name}' created."

@mcp.tool()
def insert_data(table: str, data: dict) -> str:
    """Insert a row of data into the specified table. `data` is a dict of column values."""
    cursor = conn.cursor()
    # Build columns and values for insertion
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    values = list(data.values())
    
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)
    conn.commit()
    return f"Data inserted into table '{table}'. Row ID: {cursor.lastrowid}"

@mcp.tool()
def fetch_data(query: str) -> str:
    """Fetch data by executing a SELECT query and returning the results."""
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return str(rows)

@mcp.tool()
def list_tables() -> str:
    """List all tables in the current database."""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    return str([table[0] for table in tables])

@mcp.tool()
def describe_table(table: str) -> str:
    """Show the structure of a specific table."""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table}")
    columns = cursor.fetchall()
    return str(columns)

if __name__ == "__main__":
    mcp.run()