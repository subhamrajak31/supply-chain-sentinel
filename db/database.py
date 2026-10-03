import sqlite3
import os

# Define path relative to project root
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "inventory_sentinel.db")

def init_db():
    """
    Initializes the SQLite database with schemas for suppliers, inventory,
    and active orders, then populates them with sample data.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create 'suppliers' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location_country TEXT NOT NULL,
        location_city TEXT NOT NULL,
        contact_email TEXT
    );
    """)

    # 2. Create 'inventory' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity_on_hand INTEGER NOT NULL,
        reorder_level INTEGER NOT NULL,
        unit_cost REAL NOT NULL
    );
    """)

    # 3. Create 'active_orders' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        origin_country TEXT NOT NULL,
        status TEXT NOT NULL,
        expected_delivery TEXT NOT NULL,
        FOREIGN KEY (item_id) REFERENCES inventory (item_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
    );
    """)

    # Reset tables to maintain a clean slate for testing
    cursor.execute("DELETE FROM active_orders;")
    cursor.execute("DELETE FROM inventory;")
    cursor.execute("DELETE FROM suppliers;")

    # Insert sample suppliers
    suppliers_data = [
        ("Taiwan Micro Semi", "Taiwan", "Hsinchu", "contact@twsemi.com"),
        ("Suez Logistics Parts", "Egypt", "Suez", "support@suezparts.eg"),
        ("Nordic Raw Metals", "Norway", "Oslo", "sales@nordicmetals.no")
    ]
    cursor.executemany("""
    INSERT INTO suppliers (name, location_country, location_city, contact_email)
    VALUES (?, ?, ?, ?);
    """, suppliers_data)

    # Insert sample inventory items
    inventory_data = [
        ("Microcontroller Board A1", 150, 200, 12.50),
        ("High-Pressure Seals", 800, 500, 2.10),
        ("Industrial Aluminum Sheet", 40, 100, 85.00)
    ]
    cursor.executemany("""
    INSERT INTO inventory (item_name, quantity_on_hand, reorder_level, unit_cost)
    VALUES (?, ?, ?, ?);
    """, inventory_data)

    # Insert active in-transit orders
    orders_data = [
        (1, 1, 500, "Taiwan", "IN_TRANSIT", "2026-10-15"),
        (2, 2, 2000, "Egypt", "IN_TRANSIT", "2026-10-20"),
        (3, 3, 300, "Norway", "IN_TRANSIT", "2026-11-01")
    ]
    cursor.executemany("""
    INSERT INTO active_orders (item_id, supplier_id, quantity, origin_country, status, expected_delivery)
    VALUES (?, ?, ?, ?, ?, ?);
    """, orders_data)

    conn.commit()
    conn.close()
    print("✓ Database successfully initialized at:", os.path.abspath(DB_PATH))

if __name__ == "__main__":
    init_db()