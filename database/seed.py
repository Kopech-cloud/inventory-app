# database/seed.py

from database.db import get_connection
from database.schema import create_tables


def seed_default_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = %s",
        ("admin",)
    )
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        """, ("admin", "admin123", "admin"))
        conn.commit()
        print("Default admin created: admin / admin123")
    else:
        print("Default admin already exists.")

    conn.close()


def seed_sample_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    customer_count = cursor.fetchone()["total"]

    if customer_count == 0:
        cursor.execute("""
            INSERT INTO customers (name, phone, email, address)
            VALUES
            (%s, %s, %s, %s),
            (%s, %s, %s, %s)
        """, (
            "Walk-in Customer", "08000000000", "walkin@example.com", "Ibadan",
            "Test Customer", "08111111111", "test@example.com", "Lagos"
        ))
        conn.commit()
        print("Sample customers added.")
    else:
        print("Customers already exist. Skipping sample customers.")

    cursor.execute("SELECT COUNT(*) AS total FROM products")
    product_count = cursor.fetchone()["total"]

    if product_count == 0:
        cursor.execute("""
            INSERT INTO products (name, category, price, stock_qty, status, track_serials, serial_numbers)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s, %s)
        """, (
            "ThinkDiag Mini", "Diagnostics", 50000, 10, "In Stock", 0, "[]",
            "HP EliteBook 840", "Laptop", 250000, 5, "Low Stock", 0, "[]"
        ))
        conn.commit()
        print("Sample products added.")
    else:
        print("Products already exist. Skipping sample products.")

    conn.close()


def run_seed():
    create_tables()
    seed_default_admin()
    seed_sample_data()


if __name__ == "__main__":
    run_seed()