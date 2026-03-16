# database/schema.py

from database.db import get_connection


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'staff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            price DECIMAL(12,2) NOT NULL DEFAULT 0,
            stock_qty INT NOT NULL DEFAULT 0,
            status VARCHAR(50) NOT NULL DEFAULT 'In Stock',
            track_serials TINYINT(1) NOT NULL DEFAULT 0,
            serial_numbers JSON NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            email VARCHAR(255),
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_number VARCHAR(100) NOT NULL UNIQUE,
            customer_id INT NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
            payment_status VARCHAR(50) NOT NULL DEFAULT 'UNPAID',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_invoices_customer
                FOREIGN KEY (customer_id) REFERENCES customers(id)
                ON DELETE RESTRICT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            invoice_id INT NOT NULL,
            product_id INT NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            price DECIMAL(12,2) NOT NULL DEFAULT 0,
            quantity INT NOT NULL DEFAULT 1,
            serial_number VARCHAR(255) DEFAULT '',
            line_total DECIMAL(12,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_invoice_items_invoice
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                ON DELETE CASCADE,
            CONSTRAINT fk_invoice_items_product
                FOREIGN KEY (product_id) REFERENCES products(id)
                ON DELETE RESTRICT
        )
    """)

    conn.commit()
    conn.close()