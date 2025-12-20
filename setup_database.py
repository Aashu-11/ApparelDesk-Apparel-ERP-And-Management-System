"""Run SQL setup script to create tables and sample data."""
import os
from pathlib import Path

def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

import mysql.connector

# Connection settings
config = {
    'host': os.environ.get("DB_HOST", "localhost"),
    'port': int(os.environ.get("DB_PORT", 3306)),
    'database': os.environ.get("DB_NAME", "railway"),
    'user': os.environ.get("DB_USER", "root"),
    'password': os.environ.get("DB_PASSWORD", "")
}

print(f"Connecting to {config['database']}@{config['host']}:{config['port']}...")

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    print("Connected! Creating tables...")
    
    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT PRIMARY KEY AUTO_INCREMENT,
            product_name VARCHAR(100) NOT NULL,
            product_code VARCHAR(50),
            product_category VARCHAR(50),
            product_type VARCHAR(50),
            description VARCHAR(50) NOT NULL,
            sales_price DECIMAL(10, 2),
            material VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  - products table created")
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT PRIMARY KEY AUTO_INCREMENT,
            customer_name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  - customers table created")
    
    # Create sales_orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_orders (
            sales_order_id INT PRIMARY KEY AUTO_INCREMENT,
            customer_id INT NOT NULL,
            order_date DATE NOT NULL,
            order_status VARCHAR(20) DEFAULT 'confirmed',
            total_amount DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  - sales_orders table created")
    
    # Create sales_order_lines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_order_lines (
            line_id INT PRIMARY KEY AUTO_INCREMENT,
            sales_order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            unit_price DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  - sales_order_lines table created")
    
    conn.commit()
    
    # Check if data exists
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    if product_count == 0:
        print("\nInserting sample products...")
        
        products = [
            (1, 'Classic Blue Jeans', 'JN001', 'Bottoms', 'Denim', 'jeans', 49.99),
            (2, 'Slim Fit Black Jeans', 'JN002', 'Bottoms', 'Denim', 'jeans', 59.99),
            (3, 'Relaxed Fit Jeans', 'JN003', 'Bottoms', 'Denim', 'jeans', 44.99),
            (4, 'High Waist Jeans', 'JN004', 'Bottoms', 'Denim', 'jeans', 54.99),
            (5, 'Vintage Wash Jeans', 'JN005', 'Bottoms', 'Denim', 'jeans', 64.99),
            (6, 'White Oxford Shirt', 'SH001', 'Tops', 'Formal', 'shirt', 39.99),
            (7, 'Blue Checkered Shirt', 'SH002', 'Tops', 'Casual', 'shirt', 34.99),
            (8, 'Linen Summer Shirt', 'SH003', 'Tops', 'Casual', 'shirt', 44.99),
            (9, 'Flannel Plaid Shirt', 'SH004', 'Tops', 'Casual', 'shirt', 49.99),
            (10, 'Denim Western Shirt', 'SH005', 'Tops', 'Casual', 'shirt', 54.99),
            (11, 'Basic White Tee', 'TS001', 'Tops', 'Basic', 'tshirt', 19.99),
            (12, 'Black Graphic Tee', 'TS002', 'Tops', 'Graphic', 'tshirt', 24.99),
            (13, 'Striped Tee', 'TS003', 'Tops', 'Casual', 'tshirt', 22.99),
            (14, 'V-Neck Navy Tee', 'TS004', 'Tops', 'Basic', 'tshirt', 21.99),
            (15, 'Pocket Tee Green', 'TS005', 'Tops', 'Casual', 'tshirt', 26.99),
            (16, 'White Sneakers', 'FW001', 'Footwear', 'Sneakers', 'shoes', 79.99),
            (17, 'Black Running Shoes', 'FW002', 'Footwear', 'Athletic', 'shoes', 89.99),
            (18, 'Brown Leather Boots', 'FW003', 'Footwear', 'Boots', 'shoes', 129.99),
            (19, 'Canvas Slip-Ons', 'FW004', 'Footwear', 'Casual', 'shoes', 49.99),
            (20, 'High Top Sneakers', 'FW005', 'Footwear', 'Sneakers', 'shoes', 94.99),
            (21, 'Denim Jacket', 'JK001', 'Outerwear', 'Casual', 'jacket', 89.99),
            (22, 'Black Leather Jacket', 'JK002', 'Outerwear', 'Biker', 'jacket', 199.99),
            (23, 'Bomber Jacket Navy', 'JK003', 'Outerwear', 'Casual', 'jacket', 79.99),
            (24, 'Windbreaker Green', 'JK004', 'Outerwear', 'Athletic', 'jacket', 69.99),
            (25, 'Hoodie Gray', 'JK005', 'Outerwear', 'Casual', 'jacket', 59.99),
        ]
        
        for p in products:
            cursor.execute("""
                INSERT INTO products (product_id, product_name, product_code, product_category, product_type, description, sales_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, p)
        
        print(f"  - Inserted {len(products)} products")
        conn.commit()
    else:
        print(f"\nProducts already exist ({product_count} found)")
    
    # Check customers
    cursor.execute("SELECT COUNT(*) FROM customers")
    customer_count = cursor.fetchone()[0]
    
    if customer_count == 0:
        print("\nInserting sample customers...")
        for i in range(1, 301):
            cursor.execute("""
                INSERT INTO customers (customer_id, customer_name, email)
                VALUES (%s, %s, %s)
            """, (i, f'Customer_{i}', f'customer{i}@email.com'))
        print("  - Inserted 300 customers")
        conn.commit()
    else:
        print(f"Customers already exist ({customer_count} found)")
    
    # Check orders
    cursor.execute("SELECT COUNT(*) FROM sales_orders")
    order_count = cursor.fetchone()[0]
    
    if order_count == 0:
        print("\nGenerating sample orders...")
        import random
        from datetime import datetime, timedelta
        
        for i in range(500):
            customer_id = random.randint(1, 300)
            order_date = datetime.now() - timedelta(days=random.randint(1, 365))
            status = random.choice(['confirmed', 'confirmed', 'confirmed', 'invoiced'])
            
            cursor.execute("""
                INSERT INTO sales_orders (customer_id, order_date, order_status, total_amount)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, order_date.date(), status, round(50 + random.random() * 200, 2)))
            
            order_id = cursor.lastrowid
            
            # Add 1-3 products per order
            num_products = random.randint(1, 3)
            products_in_order = random.sample(range(1, 26), min(num_products, 25))
            
            for prod_id in products_in_order:
                cursor.execute("""
                    INSERT INTO sales_order_lines (sales_order_id, product_id, quantity, unit_price)
                    VALUES (%s, %s, %s, (SELECT sales_price FROM products WHERE product_id = %s))
                """, (order_id, prod_id, random.randint(1, 3), prod_id))
        
        print("  - Generated 500 orders with order lines")
        conn.commit()
    else:
        print(f"Orders already exist ({order_count} found)")
    
    # Final summary
    print("\n" + "=" * 50)
    print("DATABASE SETUP COMPLETE!")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"  Products: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    print(f"  Customers: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM sales_orders")
    print(f"  Sales Orders: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM sales_order_lines")
    print(f"  Order Lines: {cursor.fetchone()[0]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
