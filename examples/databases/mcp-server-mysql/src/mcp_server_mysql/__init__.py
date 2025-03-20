from mcp_server_mysql.server import mcp


def main():
    """Main entry point for the package."""
    mcp.run()


__all__ = ["main", "server"]

if __name__ == "__main__":
    main()