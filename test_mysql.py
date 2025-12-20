"""Test MySQL connection and data sources."""
from data.mysql_loader import MySQLDataLoader

print("=" * 50)
print("Testing MySQL Connection")
print("=" * 50)

loader = MySQLDataLoader()

if loader.connection:
    print("\n[OK] MySQL Connected!")
    
    # Test product descriptions
    descriptions = loader.get_product_descriptions()
    if descriptions:
        print(f"\nProduct Descriptions from MySQL: {len(descriptions)}")
        for pid, desc in list(descriptions.items())[:5]:
            print(f"   Product {pid}: {desc}")
    
    # Test interactions
    interactions = loader.get_user_item_interactions()
    if interactions:
        print(f"\nUser-Item Interactions from MySQL: {len(interactions)}")
        for uid, iid, score in interactions[:5]:
            print(f"   User {uid} -> Item {iid} (score: {score})")
    
    loader.close()
else:
    print("\n[FAIL] MySQL NOT connected - Using CSV fallback")
    print("  Check your .env file for DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
    
    # Show CSV data
    print("\nChecking CSV fallback data...")
    import csv
    from pathlib import Path
    csv_path = Path(__file__).parent / "data" / "item_descriptions.csv"
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"\nCSV has {len(rows)} item descriptions:")
            for row in rows[:5]:
                print(f"   Item {row['item_id']}: {row['description']}")
    else:
        print(f"\nCSV file not found at: {csv_path}")

print("\n" + "=" * 50)
