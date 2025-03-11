import psycopg2
from mcp.server.fastmcp import FastMCP
from psycopg2 import sql

PG_HOST = "localhost"
PG_PORT = "5432"
PG_USER = "postgres"
PG_PASSWORD = "postgres"
PG_DATABASE = "postgres"

conn = psycopg2.connect(
    host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD, dbname=PG_DATABASE
)
conn.autocommit = False

mcp = FastMCP(
    "PostgreSQL",
    instructions="You are a PostgreSQL database manager. You can execute queries, create tables, and insert data into the database.",
)


@mcp.tool()
def execute_query(query: str) -> str:
    """Execute an arbitrary SQL query. Returns results for SELECT, or a success message for others."""
    cur = conn.cursor()
    cur.execute(query)
    command = query.strip().split()[0].lower()
    if command == "select" or command == "show" or command == "describe":
        rows = cur.fetchall()
        return str(rows)
    else:
        conn.commit()
        return "Query executed successfully."


@mcp.tool()
def create_table(name: str, schema: str) -> str:
    """Create a new table with the given name and schema (column definitions)."""
    cur = conn.cursor()
    cur.execute(
        sql.SQL("CREATE TABLE {} ({})").format(sql.Identifier(name), sql.SQL(schema))
    )
    conn.commit()
    return f"Table '{name}' created."


@mcp.tool()
def insert_data(table: str, data: dict) -> str:
    """Insert a row of data into the specified table. `data` is a dict of column values."""
    cur = conn.cursor()
    columns = [sql.Identifier(col) for col in data.keys()]
    values = [sql.Literal(val) for val in data.values()]
    insert_stmt = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
        sql.Identifier(table), sql.SQL(", ").join(columns), sql.SQL(", ").join(values)
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
