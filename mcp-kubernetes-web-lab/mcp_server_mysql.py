import os
import mysql.connector
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("erp-server", host="0.0.0.0", port=8000, stateless_http=True)

@mcp.tool()
def get_product_stock(product_code: str) -> dict:
    """Find the product name, stock quantity and price by exact product code."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "mysql.default.svc.cluster.local"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"], connection_timeout=10,
    )
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT product_code, product_name, stock, price FROM product_stock WHERE product_code = %s", (product_code.strip(),))
            product = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        conn.close()
    if product is None:
        return {"result": "NOT_FOUND", "product_code": product_code}
    return {"result": "OK", "product_code": product["product_code"],
            "name": product["product_name"], "stock": product["stock"],
            "price": str(product["price"])}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
