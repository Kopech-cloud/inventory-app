import sqlite3
import json
import pymysql
from pymysql.cursors import DictCursor

SQLITE_DB = "inventory.db"

MYSQL_CONFIG = {
    "host": "73.166.120.244",
    "user": "inventory_user",
    "password": "StrongPasswordHere123!",
    "database": "inventory_app",
    "port": 3306,
    "cursorclass": DictCursor,
    "autocommit": False,
}

def migrate():
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    s = sqlite_conn.cursor()

    mysql_conn = pymysql.connect(**MYSQL_CONFIG)
    m = mysql_conn.cursor()

    try:
        # products
        s.execute("SELECT * FROM products")
        for row in s.fetchall():
            m.execute("""
                INSERT INTO products
                (id, name, category, price, stock_qty, status, track_serials, serial_numbers, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row["id"],
                row["name"],
                row["category"],
                float(row["price"]),
                int(row["stock_qty"]),
                row["status"],
                int(row["track_serials"]) if "track_serials" in row.keys() else 0,
                row["serial_numbers"] if "serial_numbers" in row.keys() else json.dumps([]),
                row["created_at"] if "created_at" in row.keys() else None,
            ))

        # customers
        s.execute("SELECT * FROM customers")
        for row in s.fetchall():
            m.execute("""
                INSERT INTO customers
                (id, name, phone, email, address, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row["id"], row["name"], row["phone"], row["email"], row["address"], row["created_at"]
            ))

        # invoices
        s.execute("SELECT * FROM invoices")
        for row in s.fetchall():
            payment_status = row["payment_status"] if "payment_status" in row.keys() else "UNPAID"
            m.execute("""
                INSERT INTO invoices
                (id, invoice_number, customer_id, customer_name, total_amount, payment_status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["id"],
                row["invoice_number"],
                row["customer_id"],
                row["customer_name"],
                float(row["total_amount"]),
                payment_status,
                row["created_at"],
            ))

        # invoice_items
        s.execute("SELECT * FROM invoice_items")
        for row in s.fetchall():
            serial_number = row["serial_number"] if "serial_number" in row.keys() else ""
            m.execute("""
                INSERT INTO invoice_items
                (id, invoice_id, product_id, product_name, price, quantity, serial_number, line_total)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row["id"],
                row["invoice_id"],
                row["product_id"],
                row["product_name"],
                float(row["price"]),
                int(row["quantity"]),
                serial_number,
                float(row["line_total"]),
            ))

        # users
        s.execute("SELECT * FROM users")
        for row in s.fetchall():
            m.execute("""
                INSERT INTO users
                (id, username, password, role, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                row["id"], row["username"], row["password"], row["role"], row["created_at"]
            ))

        mysql_conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        mysql_conn.rollback()
        print("Migration failed:", e)
        raise

    finally:
        sqlite_conn.close()
        mysql_conn.close()

if __name__ == "__main__":
    migrate()