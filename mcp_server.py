from mcp.server.mcpserver import MCPServer

mcp = MCPServer("test-server")

# Mock ERP data
PRODUCTS = {
    "A100": {
        "name": "Printer Toner",
        "stock": 15,
        "price": 85000
    },
    "A200": {
        "name": "A4 Copy Paper",
        "stock": 120,
        "price": 25000
    },
    "A300": {
        "name": "Mouse",
        "stock": 0,
        "price": 35000
    }
}


@mcp.tool()
def get_product_stock(product_code: str) -> dict:
    """Look up the product name, current stock quantity, and price by product code."""

    product = PRODUCTS.get(product_code)

    if product is None:
        return {
            "result": "NOT_FOUND",
            "product_code": product_code
        }

    return {
        "result": "OK",
        "product_code": product_code,
        "name": product["name"],
        "stock": product["stock"],
        "price": product["price"]
    }


if __name__ == "__main__":
    mcp.run()