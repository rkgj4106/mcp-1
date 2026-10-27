CREATE TABLE IF NOT EXISTS product_stock (
  product_code VARCHAR(20) PRIMARY KEY,
  product_name VARCHAR(100) NOT NULL,
  stock INT NOT NULL,
  price DECIMAL(12,2) NOT NULL
);
INSERT INTO product_stock (product_code, product_name, stock, price)
VALUES ('A100','printer',10,10000), ('B200','computer',15,20000)
ON DUPLICATE KEY UPDATE product_name=VALUES(product_name), stock=VALUES(stock), price=VALUES(price);
