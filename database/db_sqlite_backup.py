import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "inventory.db"


def get_connection():
    conn = sqlite3.connect("inventory.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 1,
            serial_number TEXT NOT NULL DEFAULT '',
            line_total REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT '',
            address TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            customer_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            payment_status TEXT NOT NULL DEFAULT 'UNPAID',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 1,
            line_total REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    upgrade_products_table()
    upgrade_invoice_items_table()
    upgrade_invoices_table()


def upgrade_products_table():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN track_serials INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN serial_numbers TEXT NOT NULL DEFAULT '[]'")
    except Exception:
        pass

    conn.commit()
    conn.close()

def upgrade_invoice_items_table():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE invoice_items ADD COLUMN serial_number TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass

    conn.commit()
    conn.close()

def upgrade_invoices_table():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN payment_status TEXT NOT NULL DEFAULT 'UNPAID'")
    except Exception:
        pass

    conn.commit()
    conn.close()

def mark_invoice_as_paid(invoice_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE invoices
        SET payment_status = 'PAID'
        WHERE id = ?
    """, (invoice_id,))
    conn.commit()
    conn.close()

def calculate_status(stock_qty: int) -> str:
    if stock_qty <= 0:
        return "Out of Stock"
    elif stock_qty <= 5:
        return "Low Stock"
    return "In Stock"


# ---------------- PRODUCTS ----------------

def get_products(search_text: str = "", category_filter: str = "All"):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, name, category, price, stock_qty, status, track_serials, serial_numbers, created_at
        FROM products
        WHERE 1=1
    """
    params = []

    if search_text:
        query += " AND (name LIKE ? OR category LIKE ?)"
        like_value = f"%{search_text}%"
        params.extend([like_value, like_value])

    if category_filter and category_filter != "All":
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    products = []
    for row in rows:
        try:
            serials = json.loads(row["serial_numbers"]) if row["serial_numbers"] else []
        except Exception:
            serials = []

        products.append({
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "price": row["price"],
            "stock_qty": row["stock_qty"],
            "status": row["status"],
            "track_serials": bool(row["track_serials"]),
            "serial_numbers": serials,
            "created_at": row["created_at"],
        })

    return products


def get_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, category, price, stock_qty, status
        FROM products
        ORDER BY name ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_product_by_id(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, category, price, stock_qty, status, track_serials, serial_numbers, created_at
        FROM products
        WHERE id = ?
    """, (product_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    try:
        serials = json.loads(row["serial_numbers"]) if row["serial_numbers"] else []
    except Exception:
        serials = []

    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": row["price"],
        "stock_qty": row["stock_qty"],
        "status": row["status"],
        "track_serials": bool(row["track_serials"]),
        "serial_numbers": serials,
        "created_at": row["created_at"],
    }

def mark_serial_as_sold(product_id: int, sold_serial: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT stock_qty, serial_numbers
        FROM products
        WHERE id = ?
    """, (product_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return

    try:
        serials = json.loads(row["serial_numbers"]) if row["serial_numbers"] else []
    except Exception:
        serials = []

    serials = [s for s in serials if s != sold_serial]
    new_stock_qty = len(serials)
    new_status = calculate_status(new_stock_qty)

    cursor.execute("""
        UPDATE products
        SET stock_qty = ?, status = ?, serial_numbers = ?
        WHERE id = ?
    """, (
        new_stock_qty,
        new_status,
        json.dumps(serials),
        product_id
    ))

    conn.commit()
    conn.close()

def add_invoice_item(invoice_id, product_id, product_name, price, quantity, line_total, serial_number=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoice_items (
            invoice_id, product_id, product_name, price, quantity, serial_number, line_total
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_id,
        product_id,
        product_name,
        price,
        quantity,
        serial_number,
        line_total
    ))
    conn.commit()
    conn.close()

import json

def add_product(name, category, price, stock_qty, track_serials=False, serial_numbers=None):
    if serial_numbers is None:
        serial_numbers = []

    status = calculate_status(stock_qty)
    serial_numbers_json = json.dumps(serial_numbers)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, category, price, stock_qty, status, track_serials, serial_numbers)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        category,
        price,
        stock_qty,
        status,
        1 if track_serials else 0,
        serial_numbers_json
    ))
    conn.commit()
    conn.close()


def update_product(product_id: int, name: str, category: str, price: float, stock_qty: int):
    status = calculate_status(stock_qty)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products
        SET name = ?, category = ?, price = ?, stock_qty = ?, status = ?
        WHERE id = ?
    """, (name, category, price, stock_qty, status, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def update_product_stock(product_id: int, new_stock_qty: int):
    status = calculate_status(new_stock_qty)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products
        SET stock_qty = ?, status = ?
        WHERE id = ?
    """, (new_stock_qty, status, product_id))
    conn.commit()
    conn.close()

def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, ("admin", "admin123", "admin"))
        conn.commit()

    conn.close()


def authenticate_user(username: str, password: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, role
        FROM users
        WHERE username = ? AND password = ?
    """, (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def get_product_serial_statuses(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    product = get_product_by_id(product_id)
    if not product:
        conn.close()
        return []

    available_serials = product.get("serial_numbers", [])

    cursor.execute("""
        SELECT DISTINCT serial_number
        FROM invoice_items
        WHERE product_id = ? AND TRIM(serial_number) != ''
        ORDER BY serial_number ASC
    """, (product_id,))
    sold_rows = cursor.fetchall()

    conn.close()

    sold_serials = [row["serial_number"] for row in sold_rows]

    all_serials = []

    for serial in sorted(available_serials):
        all_serials.append({
            "serial_number": serial,
            "status": "Available"
        })

    for serial in sorted(sold_serials):
        if serial not in available_serials:
            all_serials.append({
                "serial_number": serial,
                "status": "Sold"
            })

    return all_serials


# ---------------- CUSTOMERS ----------------

def get_customers(search_text: str = ""):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, name, phone, email, address
        FROM customers
        WHERE 1=1
    """
    params = []

    if search_text:
        like_value = f"%{search_text}%"
        query += " AND (name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        params.extend([like_value, like_value, like_value])

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, phone, email, address
        FROM customers
        ORDER BY name ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def add_customer(name: str, phone: str, email: str, address: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO customers (name, phone, email, address)
        VALUES (?, ?, ?, ?)
    """, (name, phone, email, address))
    conn.commit()
    conn.close()


def update_customer(customer_id: int, name: str, phone: str, email: str, address: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers
        SET name = ?, phone = ?, email = ?, address = ?
        WHERE id = ?
    """, (name, phone, email, address, customer_id))
    conn.commit()
    conn.close()


def delete_customer(customer_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


def get_customer_by_id(customer_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, phone, email, address
        FROM customers
        WHERE id = ?
    """, (customer_id,))
    row = cursor.fetchone()
    conn.close()
    return row


# ---------------- INVOICES ----------------

def generate_invoice_number():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM invoices")
    total = cursor.fetchone()["total"]
    conn.close()
    return f"INV-{total + 1:05d}"


def get_invoices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, invoice_number, customer_name, total_amount, payment_status, created_at
        FROM invoices
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def create_invoice(customer_id: int, items: list):
    """
    items format:
    [
        {
            "product_id": 1,
            "product_name": "ThinkDiag Mini",
            "price": 55000,
            "quantity": 1,
            "serial_number": "TD001"
        }
    ]
    """
    if not items:
        raise ValueError("Invoice must contain at least one item.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        customer = get_customer_by_id(customer_id)
        if not customer:
            raise ValueError("Customer not found.")

        total_amount = 0
        prepared_items = []

        for item in items:
            product = get_product_by_id(item["product_id"])
            if not product:
                raise ValueError(f"Product not found: {item['product_name']}")

            quantity = int(item["quantity"])
            if quantity <= 0:
                raise ValueError(f"Invalid quantity for {product['name']}")

            serial_number = item.get("serial_number", "").strip()

            if product.get("track_serials", False):
                if quantity != 1:
                    raise ValueError(f"Serialized product {product['name']} must have quantity 1 per line.")

                available_serials = product.get("serial_numbers", [])
                if serial_number == "":
                    raise ValueError(f"Serial number is required for {product['name']}.")

                if serial_number not in available_serials:
                    raise ValueError(
                        f"Serial number {serial_number} is not available for {product['name']}."
                    )

                new_serials = [s for s in available_serials if s != serial_number]
                new_stock = len(new_serials)
            else:
                if product["stock_qty"] < quantity:
                    raise ValueError(
                        f"Not enough stock for {product['name']}. Available: {product['stock_qty']}"
                    )

                new_stock = product["stock_qty"] - quantity
                new_serials = product.get("serial_numbers", [])

            price = float(product["price"])
            line_total = price * quantity
            total_amount += line_total

            prepared_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "price": price,
                "quantity": quantity,
                "serial_number": serial_number,
                "line_total": line_total,
                "new_stock": new_stock,
                "new_serials": new_serials,
            })

        invoice_number = generate_invoice_number()

        cursor.execute("""
            INSERT INTO invoices (invoice_number, customer_id, customer_name, total_amount, payment_status)
            VALUES (?, ?, ?, ?, ?)
        """, (invoice_number, customer_id, customer["name"], total_amount, "UNPAID"))
        
        invoice_id = cursor.lastrowid

        for item in prepared_items:
            cursor.execute("""
                INSERT INTO invoice_items (
                    invoice_id, product_id, product_name, price, quantity, serial_number, line_total
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                item["product_id"],
                item["product_name"],
                item["price"],
                item["quantity"],
                item["serial_number"],
                item["line_total"],
            ))

            new_status = calculate_status(item["new_stock"])
            cursor.execute("""
                UPDATE products
                SET stock_qty = ?, status = ?, serial_numbers = ?
                WHERE id = ?
            """, (
                item["new_stock"],
                new_status,
                json.dumps(item["new_serials"]),
                item["product_id"]
            ))

        conn.commit()
        return invoice_id, invoice_number

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def find_product_by_serial(serial_number: str):
    serial_number = serial_number.strip()

    if not serial_number:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, category, price, stock_qty, status, track_serials, serial_numbers, created_at
        FROM products
        WHERE track_serials = 1
    """)
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        try:
            serials = json.loads(row["serial_numbers"]) if row["serial_numbers"] else []
        except Exception:
            serials = []

        if serial_number in serials:
            return {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "price": row["price"],
                "stock_qty": row["stock_qty"],
                "status": row["status"],
                "track_serials": bool(row["track_serials"]),
                "serial_numbers": serials,
                "created_at": row["created_at"],
                "matched_serial": serial_number,
            }

    return None

def get_product_categories():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL AND TRIM(category) != ''
        ORDER BY category ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [row["category"] for row in rows]

def find_serial_usage(serial_number: str):
    serial_number = serial_number.strip()

    if not serial_number:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    # First: check if the serial has been sold
    cursor.execute("""
        SELECT 
            ii.serial_number,
            ii.product_name,
            i.invoice_number,
            i.customer_name,
            i.created_at
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        WHERE ii.serial_number = ?
        ORDER BY ii.id DESC
        LIMIT 1
    """, (serial_number,))
    sold_row = cursor.fetchone()

    if sold_row:
        conn.close()
        return {
            "serial_number": sold_row["serial_number"],
            "product_name": sold_row["product_name"],
            "status": "Sold",
            "invoice_number": sold_row["invoice_number"],
            "customer_name": sold_row["customer_name"],
            "created_at": sold_row["created_at"],
        }

    # Second: check if the serial is still in stock
    cursor.execute("""
        SELECT id, name, serial_numbers
        FROM products
        WHERE track_serials = 1
    """)
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        try:
            serials = json.loads(row["serial_numbers"]) if row["serial_numbers"] else []
        except Exception:
            serials = []

        if serial_number in serials:
            return {
                "serial_number": serial_number,
                "product_name": row["name"],
                "status": "In Stock",
                "invoice_number": "",
                "customer_name": "",
                "created_at": "",
            }

    return None

def get_users(search_text: str = ""):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id, username, role, created_at
        FROM users
        WHERE 1=1
    """
    params = []

    if search_text:
        like_value = f"%{search_text}%"
        query += " AND (username LIKE ? OR role LIKE ?)"
        params.extend([like_value, like_value])

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_by_id(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, password, role
        FROM users
        WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def add_user(username: str, password: str, role: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, (username, password, role))
    conn.commit()
    conn.close()


def update_user(user_id: int, username: str, password: str, role: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET username = ?, password = ?, role = ?
        WHERE id = ?
    """, (username, password, role, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
def get_total_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM products")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def get_low_stock_products_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM products WHERE stock_qty > 0 AND stock_qty <= 5")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def get_total_customers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM customers")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def get_total_invoices():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM invoices")
    total = cursor.fetchone()["total"]
    conn.close()
    return total


def get_total_sales():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS total FROM invoices")
    total = cursor.fetchone()["total"]
    conn.close()
    return float(total)


def get_recent_invoices(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT invoice_number, customer_name, total_amount, created_at
        FROM invoices
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_low_stock_products(limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, category, stock_qty, status
        FROM products
        WHERE stock_qty > 0 AND stock_qty <= 5
        ORDER BY stock_qty ASC, name ASC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_invoice_by_id(invoice_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, invoice_number, customer_id, customer_name, total_amount, payment_status, created_at
        FROM invoices
        WHERE id = ?
    """, (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_invoice_items(invoice_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT product_name, price, quantity, serial_number, line_total
        FROM invoice_items
        WHERE invoice_id = ?
        ORDER BY id ASC
    """, (invoice_id,))
    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        items.append({
            "product_name": row["product_name"],
            "price": row["price"],
            "quantity": row["quantity"],
            "serial_number": row["serial_number"],
            "line_total": row["line_total"],
        })

    return items
