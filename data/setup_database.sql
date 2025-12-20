-- =============================================
-- Recommendation System Database Schema
-- Run this in your Railway MySQL database
-- =============================================

-- Products table (for item descriptions)
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    product_code VARCHAR(50),
    product_category VARCHAR(50),
    product_type VARCHAR(50),
    description VARCHAR(50) NOT NULL,  -- Used for outfit matching (jeans, shirt, etc.)
    sales_price DECIMAL(10, 2),
    material VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales Orders table
CREATE TABLE IF NOT EXISTS sales_orders (
    sales_order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    order_status VARCHAR(20) DEFAULT 'confirmed',
    total_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Sales Order Lines table (links orders to products)
CREATE TABLE IF NOT EXISTS sales_order_lines (
    line_id INT PRIMARY KEY AUTO_INCREMENT,
    sales_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(sales_order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- =============================================
-- Sample Products (25 items - 5 categories)
-- =============================================
INSERT INTO products (product_id, product_name, product_code, product_category, product_type, description, sales_price, material) VALUES
-- Jeans (5 items)
(1, 'Classic Blue Jeans', 'JN001', 'Bottoms', 'Denim', 'jeans', 49.99, 'Cotton Denim'),
(2, 'Slim Fit Black Jeans', 'JN002', 'Bottoms', 'Denim', 'jeans', 59.99, 'Stretch Denim'),
(3, 'Relaxed Fit Jeans', 'JN003', 'Bottoms', 'Denim', 'jeans', 44.99, 'Cotton Denim'),
(4, 'High Waist Jeans', 'JN004', 'Bottoms', 'Denim', 'jeans', 54.99, 'Premium Denim'),
(5, 'Vintage Wash Jeans', 'JN005', 'Bottoms', 'Denim', 'jeans', 64.99, 'Organic Cotton'),

-- Shirts (5 items)
(6, 'White Oxford Shirt', 'SH001', 'Tops', 'Formal', 'shirt', 39.99, 'Cotton'),
(7, 'Blue Checkered Shirt', 'SH002', 'Tops', 'Casual', 'shirt', 34.99, 'Cotton Blend'),
(8, 'Linen Summer Shirt', 'SH003', 'Tops', 'Casual', 'shirt', 44.99, 'Linen'),
(9, 'Flannel Plaid Shirt', 'SH004', 'Tops', 'Casual', 'shirt', 49.99, 'Cotton Flannel'),
(10, 'Denim Western Shirt', 'SH005', 'Tops', 'Casual', 'shirt', 54.99, 'Denim'),

-- T-Shirts (5 items)
(11, 'Basic White Tee', 'TS001', 'Tops', 'Basic', 'tshirt', 19.99, 'Cotton'),
(12, 'Black Graphic Tee', 'TS002', 'Tops', 'Graphic', 'tshirt', 24.99, 'Cotton'),
(13, 'Striped Tee', 'TS003', 'Tops', 'Casual', 'tshirt', 22.99, 'Cotton Jersey'),
(14, 'V-Neck Navy Tee', 'TS004', 'Tops', 'Basic', 'tshirt', 21.99, 'Cotton'),
(15, 'Pocket Tee Green', 'TS005', 'Tops', 'Casual', 'tshirt', 26.99, 'Organic Cotton'),

-- Shoes (5 items)
(16, 'White Sneakers', 'FW001', 'Footwear', 'Sneakers', 'shoes', 79.99, 'Leather'),
(17, 'Black Running Shoes', 'FW002', 'Footwear', 'Athletic', 'shoes', 89.99, 'Mesh'),
(18, 'Brown Leather Boots', 'FW003', 'Footwear', 'Boots', 'shoes', 129.99, 'Genuine Leather'),
(19, 'Canvas Slip-Ons', 'FW004', 'Footwear', 'Casual', 'shoes', 49.99, 'Canvas'),
(20, 'High Top Sneakers', 'FW005', 'Footwear', 'Sneakers', 'shoes', 94.99, 'Leather/Suede'),

-- Jackets (5 items)
(21, 'Denim Jacket', 'JK001', 'Outerwear', 'Casual', 'jacket', 89.99, 'Denim'),
(22, 'Black Leather Jacket', 'JK002', 'Outerwear', 'Biker', 'jacket', 199.99, 'Genuine Leather'),
(23, 'Bomber Jacket Navy', 'JK003', 'Outerwear', 'Casual', 'jacket', 79.99, 'Nylon'),
(24, 'Windbreaker Green', 'JK004', 'Outerwear', 'Athletic', 'jacket', 69.99, 'Polyester'),
(25, 'Hoodie Gray', 'JK005', 'Outerwear', 'Casual', 'jacket', 59.99, 'Cotton Fleece');

-- =============================================
-- Sample Customers (300 customers)
-- =============================================
INSERT INTO customers (customer_id, customer_name, email) VALUES
(1, 'John Smith', 'john.smith@email.com'),
(2, 'Jane Doe', 'jane.doe@email.com'),
(3, 'Bob Wilson', 'bob.wilson@email.com'),
(4, 'Alice Brown', 'alice.brown@email.com'),
(5, 'Charlie Davis', 'charlie.davis@email.com');

-- Generate more customers (6-300)
INSERT INTO customers (customer_name, email)
SELECT 
    CONCAT('Customer_', seq.n),
    CONCAT('customer', seq.n, '@email.com')
FROM (
    SELECT a.N + b.N * 10 + c.N * 100 + 6 as n
    FROM 
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
         UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
         UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
        (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2) c
    WHERE a.N + b.N * 10 + c.N * 100 + 6 <= 300
) seq;

-- =============================================
-- Sample Sales Orders and Order Lines
-- This creates purchase patterns for the recommender
-- =============================================

-- Create a stored procedure to generate sample orders
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS generate_sample_orders()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE order_id INT;
    DECLARE cust_id INT;
    DECLARE prod1 INT;
    DECLARE prod2 INT;
    
    -- Generate 500 orders with varied patterns
    WHILE i <= 500 DO
        SET cust_id = FLOOR(1 + RAND() * 300);
        
        -- Insert order
        INSERT INTO sales_orders (customer_id, order_date, order_status, total_amount)
        VALUES (cust_id, DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND() * 365) DAY), 
                IF(RAND() > 0.1, 'confirmed', 'invoiced'), 
                ROUND(50 + RAND() * 200, 2));
        
        SET order_id = LAST_INSERT_ID();
        
        -- Add 1-3 products per order
        SET prod1 = FLOOR(1 + RAND() * 25);
        INSERT INTO sales_order_lines (sales_order_id, product_id, quantity, unit_price)
        SELECT order_id, prod1, FLOOR(1 + RAND() * 3), sales_price 
        FROM products WHERE product_id = prod1;
        
        -- 60% chance of second product
        IF RAND() > 0.4 THEN
            SET prod2 = FLOOR(1 + RAND() * 25);
            IF prod2 != prod1 THEN
                INSERT INTO sales_order_lines (sales_order_id, product_id, quantity, unit_price)
                SELECT order_id, prod2, FLOOR(1 + RAND() * 2), sales_price 
                FROM products WHERE product_id = prod2;
            END IF;
        END IF;
        
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;

-- Run the procedure
CALL generate_sample_orders();

-- Drop the procedure (cleanup)
DROP PROCEDURE IF EXISTS generate_sample_orders;

-- =============================================
-- Verify data
-- =============================================
SELECT 'Products' as table_name, COUNT(*) as count FROM products
UNION ALL
SELECT 'Customers', COUNT(*) FROM customers  
UNION ALL
SELECT 'Sales Orders', COUNT(*) FROM sales_orders
UNION ALL
SELECT 'Order Lines', COUNT(*) FROM sales_order_lines;
