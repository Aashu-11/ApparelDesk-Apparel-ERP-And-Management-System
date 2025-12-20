"""
MySQL Data Loader for Recommendation System.
Fetches product descriptions and user-item interactions from MySQL database.
No C++ build tools required - uses pure Python mysql-connector.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


class MySQLDataLoader:
    """
    Loads recommendation data from MySQL database.
    
    Tables used:
    - products: product_id, description (item type)
    - customers: customer_id (user_id)
    - sales_orders: links customers to orders
    - sales_order_lines: links orders to products with quantities
    """
    
    def __init__(self):
        """Initialize database connection."""
        load_env()
        
        self.host = os.environ.get("DB_HOST", "localhost")
        self.port = int(os.environ.get("DB_PORT", 3306))
        self.database = os.environ.get("DB_NAME", "pd")
        self.user = os.environ.get("DB_USER", "root")
        self.password = os.environ.get("DB_PASSWORD", "")
        
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print(f"[MySQL] Connected to {self.database}@{self.host}:{self.port}")
        except ImportError:
            print("[MySQL] ERROR: mysql-connector-python not installed!")
            print("  Install with: pip install mysql-connector-python")
            self.connection = None
        except Exception as e:
            print(f"[MySQL] Connection failed: {e}")
            self.connection = None
    
    def get_product_descriptions(self) -> Dict[str, str]:
        """
        Fetch product_id -> description mapping from products table.
        
        Returns:
            Dict mapping product_id (str) to description (str)
            Example: {"1": "tshirt", "14": "jeans", "25": "sneakers"}
        """
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT product_id, description 
                FROM products 
                WHERE is_active = TRUE
            """)
            
            descriptions = {}
            for product_id, description in cursor.fetchall():
                descriptions[str(product_id)] = description.lower().strip()
            
            cursor.close()
            print(f"[MySQL] Loaded {len(descriptions)} product descriptions")
            return descriptions
            
        except Exception as e:
            print(f"[MySQL] Error fetching products: {e}")
            return {}
    
    def get_user_item_interactions(self) -> List[Tuple[int, int, float]]:
        """
        Fetch user-item interactions from sales orders.
        
        Returns:
            List of (user_id, item_id, score) tuples
            Score = sum of quantities purchased
        """
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    so.customer_id AS user_id,
                    sol.product_id AS item_id,
                    SUM(sol.quantity) AS score
                FROM sales_orders so
                JOIN sales_order_lines sol ON so.sales_order_id = sol.sales_order_id
                WHERE so.order_status IN ('confirmed', 'invoiced')
                GROUP BY so.customer_id, sol.product_id
                ORDER BY user_id, item_id
            """)
            
            interactions = []
            for user_id, item_id, score in cursor.fetchall():
                interactions.append((int(user_id), int(item_id), float(score)))
            
            cursor.close()
            print(f"[MySQL] Loaded {len(interactions)} user-item interactions")
            return interactions
            
        except Exception as e:
            print(f"[MySQL] Error fetching interactions: {e}")
            return []
    
    def get_product_details(self, product_id: int) -> Optional[Dict]:
        """Get full product details by ID."""
        if not self.connection:
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT product_id, product_name, product_code, 
                       product_category, product_type, description,
                       sales_price, material
                FROM products 
                WHERE product_id = %s
            """, (product_id,))
            
            result = cursor.fetchone()
            cursor.close()
            return result
            
        except Exception as e:
            print(f"[MySQL] Error fetching product {product_id}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if database connection is working."""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            cursor.close()
            print(f"[MySQL] Connection OK - {count} products in database")
            return True
        except Exception as e:
            print(f"[MySQL] Connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("[MySQL] Connection closed")


# Utility function to export MySQL data to CSV (for backup/offline use)
def export_descriptions_to_csv(output_path: str = "data/item_descriptions.csv"):
    """Export product descriptions from MySQL to CSV."""
    loader = MySQLDataLoader()
    descriptions = loader.get_product_descriptions()
    loader.close()
    
    if not descriptions:
        print("No descriptions to export!")
        return
    
    import csv
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["item_id", "description"])
        for item_id, desc in sorted(descriptions.items(), key=lambda x: int(x[0])):
            writer.writerow([item_id, desc])
    
    print(f"Exported {len(descriptions)} descriptions to {output_path}")


if __name__ == "__main__":
    # Test the loader
    loader = MySQLDataLoader()
    
    if loader.test_connection():
        print("\n--- Product Descriptions ---")
        descriptions = loader.get_product_descriptions()
        for pid, desc in list(descriptions.items())[:5]:
            print(f"  Product {pid}: {desc}")
        
        print("\n--- User-Item Interactions ---")
        interactions = loader.get_user_item_interactions()
        for uid, iid, score in interactions[:5]:
            print(f"  User {uid} -> Item {iid} (score: {score})")
    
    loader.close()
