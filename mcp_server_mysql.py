from mcp.server.mcpserver import MCPServer
import mysql.connector


mcp = MCPServer("erp-server")


# --------------------------------
# MySQL Connection
# --------------------------------

# def get_db_connection():

#     return mysql.connector.connect(
#         host="localhost",
#         port=3306,
#         user="root",
#         password="byby3845",
#         database="erpdb"
#     )

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        port=13306,
        user="stud12",
        password="stud12",
        database="stud12"
    )
# def get_db_connection():

#     return mysql.connector.connect(
#         host="202.70.34.3",
#         port=30100,
#         user="stud12",
#         password="stud12",
#         database="stud12"
#     )

# --------------------------------
# MCP Tool
# --------------------------------

@mcp.tool()
def get_product_stock(product_code: str) -> dict:
    """
    Look up the product name, current stock quantity,
    and price using the product code.
    """

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            product_code,
            product_name,
            stock,
            price
        FROM product_stock
        WHERE product_code = %s
    """

    cursor.execute(sql, (product_code,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if product is None:

        return {
            "result": "NOT_FOUND",
            "product_code": product_code
        }

    return {
        "result": "OK",
        "product_code": product["product_code"],
        "name": product["product_name"],
        "stock": product["stock"],
        "price": product["price"]
    }


if __name__ == "__main__":

    mcp.run()