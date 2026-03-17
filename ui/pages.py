from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
    QHeaderView,
)


from database.db import (
    add_customer,
    add_product,
    add_user,
    create_invoice,
    delete_customer,
    delete_product,
    delete_user,
    get_all_customers,
    get_all_products,
    get_customer_by_id,
    get_customers,
    get_invoice_by_id,
    get_invoice_items,
    get_invoices,
    get_product_by_id,
    get_products,
    get_user_by_id,
    get_users,
    update_customer,
    update_product,
    update_user,
    find_serial_usage,
    find_product_by_serial,
    get_product_categories,
    get_product_serial_statuses,
    mark_invoice_as_paid,
    get_sales_report_summary,
    get_inventory_report_summary,
    get_low_stock_report,
    get_recent_sales_report,
    export_sales_report_to_excel,
)
from reports.invoice_pdf import export_invoice_pdf



def make_table_item(value, color=None):
    item = QTableWidgetItem(str(value))

    if color:
        item.setForeground(QColor(color))

    # Disable editing completely
    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    return item


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setModal(True)
        self.resize(500, 560)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.brand_input = QLineEdit()
        self.model_input = QLineEdit()
        self.specifications_input = QTextEdit()
        self.condition_input = QComboBox()
        self.category_input = QLineEdit()
        self.price_input = QLineEdit()
        self.stock_input = QLineEdit()

        self.track_serials_checkbox = QCheckBox()
        self.track_serials_checkbox.setChecked(True)

        self.serials_input = QTextEdit()

        self.name_input.setPlaceholderText("e.g. HP EliteBook 840 G5")
        self.brand_input.setPlaceholderText("e.g. HP")
        self.model_input.setPlaceholderText("e.g. 840 G5")
        self.specifications_input.setPlaceholderText("e.g. Core i5 / 8GB RAM / 256GB SSD")
        self.condition_input.addItems(["New", "Used", "Refurbished"])
        self.category_input.setPlaceholderText("e.g. Laptop")
        self.price_input.setPlaceholderText("e.g. 250000")
        self.stock_input.setPlaceholderText("Auto calculated from serials")
        self.serials_input.setPlaceholderText("Enter one serial number per line")

        self.specifications_input.setFixedHeight(90)
        self.serials_input.setFixedHeight(100)
        self.stock_input.setReadOnly(True)

        self.name_input.setObjectName("searchInput")
        self.brand_input.setObjectName("searchInput")
        self.model_input.setObjectName("searchInput")
        self.specifications_input.setObjectName("")
        self.condition_input.setObjectName("statusFilter")
        self.category_input.setObjectName("searchInput")
        self.price_input.setObjectName("searchInput")
        self.stock_input.setObjectName("searchInput")
        self.serials_input.setObjectName("")

        form.addRow("Product Name:", self.name_input)
        form.addRow("Brand:", self.brand_input)
        form.addRow("Model:", self.model_input)
        form.addRow("Specifications:", self.specifications_input)
        form.addRow("Condition:", self.condition_input)
        form.addRow("Category:", self.category_input)
        form.addRow("Price:", self.price_input)
        form.addRow("Track Serials:", self.track_serials_checkbox)
        form.addRow("Serial Numbers:", self.serials_input)
        form.addRow("Stock Qty:", self.stock_input)

        layout.addLayout(form)

        if product:
            self.name_input.setText(product.get("name", ""))
            self.brand_input.setText(product.get("brand", ""))
            self.model_input.setText(product.get("model", ""))
            self.specifications_input.setPlainText(product.get("specifications", ""))
            self.condition_input.setCurrentText(product.get("product_condition", "New") or "New")
            self.category_input.setText(product.get("category", ""))
            self.price_input.setText(str(product.get("price", "")))

            track_serials = product.get("track_serials", True)
            self.track_serials_checkbox.setChecked(track_serials)

            serials = product.get("serial_numbers", [])
            if isinstance(serials, list):
                self.serials_input.setPlainText("\n".join(serials))

            if track_serials:
                self.stock_input.setText(str(len(serials)))
            else:
                self.stock_input.setReadOnly(False)
                self.stock_input.setPlaceholderText("e.g. 35")
                self.stock_input.setText(str(product.get("stock_qty", 0)))

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")

        save_btn = QPushButton("Save Product")
        save_btn.setObjectName("primaryButton")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.validate_and_accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout.addStretch()
        layout.addLayout(buttons)

        self.serials_input.textChanged.connect(self.update_stock_from_serials)
        self.track_serials_checkbox.toggled.connect(self.toggle_serial_tracking)
        self.toggle_serial_tracking(self.track_serials_checkbox.isChecked())

    def toggle_serial_tracking(self, checked):
        self.serials_input.setEnabled(checked)
        self.stock_input.setReadOnly(checked)

        if checked:
            self.stock_input.setPlaceholderText("Auto calculated from serials")
            self.update_stock_from_serials()
        else:
            self.stock_input.clear()
            self.stock_input.setPlaceholderText("e.g. 35")

    def get_serial_numbers(self):
        text = self.serials_input.toPlainText().strip()
        return [line.strip() for line in text.splitlines() if line.strip()]

    def update_stock_from_serials(self):
        if self.track_serials_checkbox.isChecked():
            serials = self.get_serial_numbers()
            self.stock_input.setText(str(len(serials)))

    def get_data(self):
        track_serials = self.track_serials_checkbox.isChecked()
        serials = self.get_serial_numbers() if track_serials else []

        return {
            "name": self.name_input.text().strip(),
            "brand": self.brand_input.text().strip(),
            "model": self.model_input.text().strip(),
            "specifications": self.specifications_input.toPlainText().strip(),
            "product_condition": self.condition_input.currentText().strip(),
            "category": self.category_input.text().strip(),
            "price": float(self.price_input.text().strip()),
            "stock_qty": len(serials) if track_serials else int(self.stock_input.text().strip() or 0),
            "track_serials": track_serials,
            "serial_numbers": serials,
        }

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        category = self.category_input.text().strip()
        price_text = self.price_input.text().strip()
        track_serials = self.track_serials_checkbox.isChecked()
        serials = self.get_serial_numbers()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Product name is required.")
            self.name_input.setFocus()
            return

        if not category:
            QMessageBox.warning(self, "Validation Error", "Category is required.")
            self.category_input.setFocus()
            return

        try:
            price = float(price_text)
            if price < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Enter a valid price.")
            self.price_input.setFocus()
            return

        if track_serials:
            if len(serials) != len(set(serials)):
                QMessageBox.warning(self, "Duplicate Serial", "Duplicate serial numbers are not allowed.")
                return
            self.stock_input.setText(str(len(serials)))
        else:
            stock_text = self.stock_input.text().strip()
            try:
                stock_qty = int(stock_text)
                if stock_qty < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Enter a valid stock quantity.")
                self.stock_input.setFocus()
                return

        self.accept()


class ProductDetailsDialog(QDialog):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product

        self.setWindowTitle("Product Details")
        self.setModal(True)
        self.resize(520, 520)

        layout = QVBoxLayout(self)

        title = QLabel("Product Information")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        details = QTextEdit()
        details.setReadOnly(True)

        serials = product.get("serial_numbers", [])
        serial_text = "\n".join(serials) if serials else "None"

        details_text = (
            f"Name: {product.get('name', '')}\n"
            f"Brand: {product.get('brand', '')}\n"
            f"Model: {product.get('model', '')}\n"
            f"Condition: {product.get('product_condition', '')}\n"
            f"Category: {product.get('category', '')}\n"
            f"Price: ₦{float(product.get('price', 0)):,.2f}\n"
            f"Stock Qty: {product.get('stock_qty', 0)}\n"
            f"Status: {product.get('status', '')}\n"
            f"Track Serials: {'Yes' if product.get('track_serials') else 'No'}\n\n"
            f"Specifications:\n{product.get('specifications', '') or 'None'}\n\n"
            f"Serial Numbers:\n{serial_text}"
        )

        details.setText(details_text)
        layout.addWidget(details)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        
class SerialSelectionDialog(QDialog):
    def __init__(self, serial_numbers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Serial Number")
        self.setModal(True)
        self.resize(320, 220)

        layout = QVBoxLayout(self)

        label = QLabel("Choose the serial number to sell:")
        layout.addWidget(label)

        self.serial_combo = QComboBox()
        self.serial_combo.addItems(serial_numbers)
        self.serial_combo.setCurrentIndex(0)
        self.serial_combo.setMinimumHeight(38)
        self.serial_combo.setStyleSheet("""
            QComboBox {
                color: black;
                background-color: white;
                border: 1px solid #bfc5cc;
                border-radius: 8px;
                padding: 6px 10px;
                min-width: 220px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #dbeafe;
                selection-color: black;
                border: 1px solid #bfc5cc;
            }
        """)
        layout.addWidget(self.serial_combo)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("primaryButton")

        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(ok_btn)

        layout.addStretch()
        layout.addLayout(buttons)

    def get_selected_serial(self):
        return self.serial_combo.currentText().strip()
    
    
class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Edit Customer" if customer else "Add Customer")
        self.setModal(True)
        self.resize(450, 320)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setFixedHeight(90)

        self.name_input.setPlaceholderText("e.g. Bola Enterprises")
        self.phone_input.setPlaceholderText("e.g. 08012345678")
        self.email_input.setPlaceholderText("e.g. example@email.com")

        if customer:
            self.name_input.setText(customer["name"])
            self.phone_input.setText(customer["phone"])
            self.email_input.setText(customer["email"])
            self.address_input.setPlainText(customer["address"])

        form.addRow("Customer Name:", self.name_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Address:", self.address_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")

        save_btn = QPushButton("Save Customer")
        save_btn.setObjectName("primaryButton")

        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.validate_and_accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout.addStretch()
        layout.addLayout(buttons)

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        address = self.address_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Missing Data", "Customer name is required.")
            return

        self.customer_data = {
            "name": name,
            "phone": phone,
            "email": email,
            "address": address,
        }
        self.accept()


class UserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Edit User" if user else "Add User")
        self.setModal(True)
        self.resize(420, 260)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.role_input = QComboBox()

        self.username_input.setPlaceholderText("Username")
        self.password_input.setPlaceholderText("Password")

        self.username_input.setObjectName("searchInput")
        self.password_input.setObjectName("searchInput")

        self.role_input.setObjectName("statusFilter")
        self.role_input.addItems(["admin", "staff"])
        self.role_input.setCurrentIndex(0)
        
        if user:
            self.username_input.setText(user["username"])
            self.password_input.setText(user["password"])
            self.role_input.setCurrentText(user["role"])

        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        form.addRow("Role:", self.role_input)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        save_btn = QPushButton("Save User")
        save_btn.setObjectName("primaryButton")

        cancel_btn.clicked.connect(self.reject)
        
        save_btn.clicked.connect(self.validate_and_accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)

        layout.addStretch()
        layout.addLayout(buttons)

    def validate_and_accept(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing Data", "Username and password are required.")
            return

        self.user_data = {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text().strip(),
            "role": self.role_input.currentText().strip(),
        }
        self.accept()


class InvoiceDetailsDialog(QDialog):
    def __init__(self, invoice, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        self.items = get_invoice_items(invoice["id"])

        self.setWindowTitle(f"Invoice {invoice['invoice_number']}")
        self.resize(700, 450)

        layout = QVBoxLayout(self)

        info = QLabel(
            f"Customer: {invoice['customer_name']}\n"
            f"Date: {invoice['created_at']}\n"
            f"Invoice Number: {invoice['invoice_number']}\n"
            f"Status: {invoice['payment_status'] if 'payment_status' in invoice.keys() else 'UNPAID'}"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("productsTable")
        self.table.setHorizontalHeaderLabels(["Product", "Price", "Qty", "Total"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setWordWrap(False)
        layout.addWidget(self.table)

        total = 0.0
        for row, row_data in enumerate(self.items):
            self.table.insertRow(row)

            values = [
                row_data["product_name"],
                f"₦{float(row_data['price']):,.2f}",
                str(row_data["quantity"]),
                f"₦{float(row_data['line_total']):,.2f}",
            ]

            for col, value in enumerate(values):
                self.table.setItem(row, col, make_table_item(value))

            total += float(row_data["line_total"])

        self.table.resizeColumnsToContents()

        total_label = QLabel(f"Total: ₦{total:,.2f}")
        total_label.setObjectName("sectionTitle")
        layout.addWidget(total_label)

        button_row = QHBoxLayout()

        export_btn = QPushButton("Export PDF")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self.export_pdf)

        payment_status = invoice["payment_status"] if "payment_status" in invoice.keys() else "UNPAID"
        if str(payment_status).upper() == "PAID":
            export_btn.setText("Export Receipt PDF")
        else:
            export_btn.setText("Export Invoice PDF")

        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.accept)

        button_row.addStretch()
        button_row.addWidget(export_btn)
        button_row.addWidget(close_btn)

        layout.addLayout(button_row)

    def export_pdf(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Invoice")
        if not folder:
            return

        try:
            file_path = export_invoice_pdf(self.invoice, self.items, output_dir=folder)

            payment_status = (
                self.invoice["payment_status"]
                if "payment_status" in self.invoice.keys()
                else "UNPAID"
            )
            doc_label = "Receipt" if str(payment_status).upper() == "PAID" else "Invoice"

            QMessageBox.information(
                self,
                "PDF Exported",
                f"{doc_label} exported successfully:\n{file_path}",
            )
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))


class PageContainer(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("pageContainer")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        self.layout.addWidget(title_label)


class DashboardPage(PageContainer):
    def __init__(self):
        super().__init__("Dashboard Overview")

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        for text in ["Total Products", "Low Stock", "Pending Invoices"]:
            card = QFrame()
            card.setObjectName("miniCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 16, 16, 16)

            number = QLabel("0")
            number.setObjectName("miniCardNumber")

            label = QLabel(text)
            label.setObjectName("miniCardLabel")

            card_layout.addWidget(number)
            card_layout.addWidget(label)
            stats_row.addWidget(card)

        self.layout.addLayout(stats_row)

        placeholder = QLabel("Dashboard charts and summaries will go here.")
        placeholder.setObjectName("pagePlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(placeholder)


class ProductsPage(PageContainer):
    def __init__(self, current_user):
        super().__init__("Products")
        self.current_user = current_user

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by product name or category...")
        self.search_input.setObjectName("searchInput")

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("statusFilter")
        self.status_filter.addItems(["All", "In Stock", "Low Stock", "Out of Stock"])

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("secondaryButton")

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("secondaryButton")

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(self.status_filter)
        top_row.addWidget(self.search_btn)
        top_row.addWidget(self.clear_btn)

        self.layout.addLayout(top_row)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.add_btn = QPushButton("Add Product")
        self.add_btn.setObjectName("primaryButton")

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.setObjectName("secondaryButton")

        self.view_btn = QPushButton("View Product")
        self.view_btn.setObjectName("secondaryButton")

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("dangerButton")

        actions.addWidget(self.add_btn)
        actions.addWidget(self.view_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()

        self.layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setObjectName("productsTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Product Name", "Category", "Price", "Stock Qty", "Status"]
        )

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(80)

        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 140)

        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)

        self.layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.open_add_dialog)
        self.view_btn.clicked.connect(self.view_selected_product)
        self.edit_btn.clicked.connect(self.edit_selected_product)
        self.delete_btn.clicked.connect(self.delete_selected_product)
        self.search_btn.clicked.connect(self.load_products)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.status_filter.currentTextChanged.connect(self.load_products)
        self.search_input.returnPressed.connect(self.load_products)
        self.table.cellDoubleClicked.connect(self.open_product_details)

        self.load_category_filter()
        self.apply_permissions()
        self.load_products()

    def apply_permissions(self):
        role = (self.current_user or {}).get("role", "").strip().lower()
        print("PRODUCTS PAGE ROLE:", repr(role))

        is_admin = role == "admin"
        is_staff = role == "staff"

        self.add_btn.setVisible(is_admin or is_staff)
        self.edit_btn.setVisible(is_admin)
        self.delete_btn.setVisible(is_admin)

    def get_selected_product_id(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

        item = self.table.item(selected_row, 0)
        if not item:
            return None

        return int(item.text())

    def load_products(self):
        search_text = self.search_input.text().strip()
        category_text = self.status_filter.currentText()

        products = get_products(search_text=search_text, category_filter=category_text)
        self.table.setRowCount(0)

        for row_index, product in enumerate(products):
            self.table.insertRow(row_index)

            values = [
                str(product["id"]),
                product["name"],
                product["category"],
                f"₦{float(product['price']):,.2f}",
                str(product["stock_qty"]),
                product["status"],
            ]

            for col_index, value in enumerate(values):
                if col_index == 5:
                    status_value = str(value).lower()
                    if status_value == "in stock":
                        item = make_table_item(value, Qt.darkGreen)
                    elif status_value == "low stock":
                        item = make_table_item(value, Qt.darkYellow)
                    elif status_value == "out of stock":
                        item = make_table_item(value, Qt.red)
                    else:
                        item = make_table_item(value)
                else:
                    item = make_table_item(value)

                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_index, col_index, item)

        self.table.resizeRowsToContents()

    def clear_filters(self):
        self.search_input.clear()
        self.status_filter.setCurrentText("All")
        self.load_products()

    def open_add_dialog(self):
        role = (self.current_user or {}).get("role", "").strip().lower()
        if role not in ["admin", "staff"]:
            QMessageBox.warning(self, "Access Denied", "You do not have permission to add products.")
            return

        dialog = ProductDialog(self)

        if dialog.exec():
            data = dialog.get_data()

            add_product(
                name=data["name"],
                brand=data["brand"],
                model=data["model"],
                specifications=data["specifications"],
                product_condition=data["product_condition"],
                category=data["category"],
                price=data["price"],
                stock_qty=data["stock_qty"],
                track_serials=data["track_serials"],
                serial_numbers=data["serial_numbers"],
            )
            self.load_products()
            QMessageBox.information(self, "Success", "Product added successfully.")
            
    def edit_selected_product(self):
        if not self.current_user or self.current_user.get("role") != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can perform this action.")
            return

        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to edit.")
            return

        product = get_product_by_id(product_id)
        if not product:
            QMessageBox.warning(self, "Not Found", "Selected product could not be found.")
            self.load_products()
            return

        dialog = ProductDialog(self, product=product)
        if dialog.exec():
            data = dialog.get_data()
            update_product(
                product_id=product_id,
                name=data["name"],
                brand=data["brand"],
                model=data["model"],
                specifications=data["specifications"],
                product_condition=data["product_condition"],
                category=data["category"],
                price=data["price"],
                stock_qty=data["stock_qty"],
            )
            self.load_products()
            QMessageBox.information(self, "Success", "Product updated successfully.")

    def delete_selected_product(self):
        if not self.current_user or self.current_user.get("role") != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can perform this action.")
            return

        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this product?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            delete_product(product_id)
            self.load_products()
            QMessageBox.information(self, "Deleted", "Product deleted successfully.")

    def load_category_filter(self):
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("All")

        categories = get_product_categories()
        for category in categories:
            self.status_filter.addItem(category)

        self.status_filter.blockSignals(False)

    def open_product_details(self, row, column):
        item = self.table.item(row, 0)
        if not item:
            return

        try:
            product_id = int(item.text())
        except ValueError:
            return

        product = get_product_by_id(product_id)
        if not product:
            QMessageBox.warning(self, "Not Found", "Product not found.")
            return

        dialog = ProductDetailsDialog(product, self)

    def view_selected_product(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to view.")
            return

        product = get_product_by_id(product_id)
        if not product:
            QMessageBox.warning(self, "Not Found", "Selected product could not be found.")
            self.load_products()
            return

        dialog = ProductDetailsDialog(product, self)
        dialog.exec()

    def apply_permissions(self):
        role = str((self.current_user or {}).get("role", "")).strip().lower()
        print("PRODUCTS PAGE ROLE:", repr(role))

        can_add = role in ["admin", "staff"]
        can_view = role in ["admin", "staff"]
        can_edit_delete = role == "admin"

        self.add_btn.show() if can_add else self.add_btn.hide()
        self.view_btn.show() if can_view else self.view_btn.hide()
        self.edit_btn.show() if can_edit_delete else self.edit_btn.hide()
        self.delete_btn.show() if can_edit_delete else self.delete_btn.hide()

    


class CustomersPage(PageContainer):
    def __init__(self, current_user):
        super().__init__("Customers")
        self.current_user = current_user

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, phone, or email...")
        self.search_input.setObjectName("searchInput")

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("secondaryButton")

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("secondaryButton")

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(self.search_btn)
        top_row.addWidget(self.clear_btn)

        self.layout.addLayout(top_row)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.add_btn = QPushButton("Add Customer")
        self.add_btn.setObjectName("primaryButton")

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.setObjectName("secondaryButton")

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("dangerButton")

        actions.addWidget(self.add_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()

        self.layout.addLayout(actions)

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("productsTable")
        self.table.setHorizontalHeaderLabels(
            ["ID", "Customer Name", "Phone", "Email", "Address"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(180)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setWordWrap(False)

        self.layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.edit_selected_customer)
        self.delete_btn.clicked.connect(self.delete_selected_customer)
        self.search_btn.clicked.connect(self.load_customers)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.search_input.returnPressed.connect(self.load_customers)

        self.apply_permissions()
        self.load_customers()

    def apply_permissions(self):
        role = (self.current_user or {}).get("role", "").lower()
        is_admin = role == "admin"
        is_staff = role == "staff"

        self.add_btn.setVisible(is_admin or is_staff)
        self.edit_btn.setVisible(is_admin)
        self.delete_btn.setVisible(is_admin)

    def get_selected_customer_id(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

        item = self.table.item(selected_row, 0)
        if not item:
            return None

        return int(item.text())

    def load_customers(self):
        search_text = self.search_input.text().strip()
        customers = get_customers(search_text=search_text)

        self.table.setRowCount(0)

        for row_index, customer in enumerate(customers):
            self.table.insertRow(row_index)

            values = [
                str(customer["id"]),
                customer["name"],
                customer["phone"],
                customer["email"] or "",
                customer["address"] or "",
            ]

            for col_index, value in enumerate(values):
                item = make_table_item(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_index, col_index, item)

        self.table.resizeRowsToContents()

    def clear_filters(self):
        self.search_input.clear()
        self.load_customers()

    def open_add_dialog(self):
        dialog = CustomerDialog(self)

        if dialog.exec():
            data = dialog.customer_data
            add_customer(
                name=data["name"],
                phone=data["phone"],
                email=data["email"],
                address=data["address"],
            )
            self.load_customers()
            QMessageBox.information(self, "Success", "Customer added successfully.")

    def edit_selected_customer(self):
        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a customer to edit.")
            return

        customer = get_customer_by_id(customer_id)
        if not customer:
            QMessageBox.warning(self, "Not Found", "Selected customer could not be found.")
            self.load_customers()
            return

        dialog = CustomerDialog(self, customer=customer)

        if dialog.exec():
            data = dialog.customer_data
            update_customer(
                customer_id=customer_id,
                name=data["name"],
                phone=data["phone"],
                email=data["email"],
                address=data["address"],
            )
            self.load_customers()
            QMessageBox.information(self, "Success", "Customer updated successfully.")

    def delete_selected_customer(self):
        role = (self.current_user or {}).get("role", "").lower()
        if role != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can delete customers.")
            return

        customer_id = self.get_selected_customer_id()
        if customer_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a customer to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this customer?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            delete_customer(customer_id)
            self.load_customers()
            QMessageBox.information(self, "Deleted", "Customer deleted successfully.")


class InvoicesPage(PageContainer):
    def __init__(self, current_user):
        super().__init__("Invoices")
        self.current_user = current_user

        top_actions = QHBoxLayout()
        top_actions.setSpacing(10)

        self.customer_combo = QComboBox()
        self.customer_combo.setObjectName("statusFilter")

        self.product_combo = QComboBox()
        self.product_combo.setObjectName("statusFilter")

        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("Qty")
        self.qty_input.setObjectName("searchInput")
        self.qty_input.setFixedWidth(100)

        self.add_item_btn = QPushButton("Add Item")
        self.add_item_btn.setObjectName("primaryButton")

        top_actions.addWidget(QLabel("Customer:"))
        top_actions.addWidget(self.customer_combo, 1)
        top_actions.addWidget(QLabel("Product:"))
        top_actions.addWidget(self.product_combo, 1)
        top_actions.addWidget(self.qty_input)
        top_actions.addWidget(self.add_item_btn)

        scan_row = QHBoxLayout()
        scan_row.setSpacing(10)

        self.scan_serial_input = QLineEdit()
        self.scan_serial_input.setPlaceholderText("Scan or enter serial to add item")
        self.scan_serial_input.setObjectName("searchInput")
        self.scan_serial_input.returnPressed.connect(self.add_scanned_serial_to_invoice)

        self.scan_serial_btn = QPushButton("Scan Add")
        self.scan_serial_btn.setObjectName("primaryButton")
        self.scan_serial_btn.clicked.connect(self.add_scanned_serial_to_invoice)

        scan_row.addWidget(QLabel("Scan Serial:"))
        scan_row.addWidget(self.scan_serial_input, 1)
        scan_row.addWidget(self.scan_serial_btn)

        self.layout.addLayout(scan_row)
        self.layout.addLayout(top_actions)

        self.items_table = QTableWidget(0, 6)
        self.items_table.setObjectName("productsTable")
        self.items_table.setHorizontalHeaderLabels(
            ["Product ID", "Product Name", "Serial No", "Price", "Quantity", "Line Total"]
        )
        self.items_table.horizontalHeader().setStretchLastSection(True)
        self.items_table.horizontalHeader().setDefaultSectionSize(140)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setWordWrap(False)

        self.layout.addWidget(self.items_table)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.remove_item_btn = QPushButton("Remove Selected Item")
        self.remove_item_btn.setObjectName("dangerButton")

        self.total_label = QLabel("Total: ₦0.00")
        self.total_label.setObjectName("sectionTitle")

        self.save_invoice_btn = QPushButton("Save Invoice")
        self.save_invoice_btn.setObjectName("primaryButton")

        self.mark_paid_btn = QPushButton("Mark Invoice Paid")
        self.mark_paid_btn.setObjectName("secondaryButton")

        bottom_row.addWidget(self.remove_item_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(self.total_label)
        bottom_row.addWidget(self.mark_paid_btn)
        bottom_row.addWidget(self.save_invoice_btn)

        self.layout.addLayout(bottom_row)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)

        self.serial_search_input = QLineEdit()
        self.serial_search_input.setPlaceholderText("Enter serial number to search")
        self.serial_search_input.setObjectName("searchInput")

        self.serial_search_btn = QPushButton("Search Serial")
        self.serial_search_btn.setObjectName("primaryButton")
        self.serial_search_btn.clicked.connect(self.search_serial_usage)

        search_row.addWidget(self.serial_search_input)
        search_row.addWidget(self.serial_search_btn)

        self.layout.addLayout(search_row)

        self.serial_search_result = QLabel("")
        self.serial_search_result.setWordWrap(True)
        self.layout.addWidget(self.serial_search_result)

        history_title = QLabel("Invoice History")
        history_title.setObjectName("sectionTitle")
        self.layout.addWidget(history_title)

        self.invoice_table = QTableWidget(0, 6)
        self.invoice_table.setObjectName("productsTable")
        self.invoice_table.setHorizontalHeaderLabels(
            ["ID", "Invoice Number", "Customer", "Total", "Status", "Date"]
        )
        header = self.invoice_table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

        self.invoice_table.setColumnWidth(2, 320)
        self.invoice_table.setColumnWidth(4, 120)
        self.invoice_table.setColumnWidth(5, 220)

        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.invoice_table.setFocusPolicy(Qt.NoFocus)
        self.invoice_table.setWordWrap(False)
        self.invoice_table.setAlternatingRowColors(True)

        self.layout.addWidget(self.invoice_table)

        self.current_items = []

        self.add_item_btn.clicked.connect(self.add_item_to_invoice)
        self.remove_item_btn.clicked.connect(self.remove_selected_item)
        self.save_invoice_btn.clicked.connect(self.save_invoice)
        self.invoice_table.cellDoubleClicked.connect(self.open_invoice_details)
        self.mark_paid_btn.clicked.connect(self.mark_selected_invoice_paid)

        self.load_customers_dropdown()
        self.load_products_dropdown()
        self.apply_permissions()
        self.load_invoices()

        self.scan_serial_input.setFocus()

    def apply_permissions(self):
        role = (self.current_user or {}).get("role", "").lower()
        is_admin = role == "admin"

        if not is_admin:
            self.mark_paid_btn.hide()

    def mark_selected_invoice_paid(self):
        role = (self.current_user or {}).get("role", "").lower()
        if role != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can mark invoices as paid.")
            return

        row = self.invoice_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an invoice first.")
            return

        invoice_id = int(self.invoice_table.item(row, 0).text())
        current_status = self.invoice_table.item(row, 4).text().strip().upper()

        if current_status == "PAID":
            QMessageBox.information(self, "Already Paid", "This invoice is already marked as PAID.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Payment",
            "Mark this invoice as PAID?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            mark_invoice_as_paid(invoice_id)
            self.load_invoices()
            QMessageBox.information(self, "Updated", "Invoice marked as PAID.")

    def load_customers_dropdown(self):
        self.customer_combo.clear()
        customers = get_all_customers()
        for customer in customers:
            self.customer_combo.addItem(customer["name"], customer["id"])

    def load_products_dropdown(self):
        self.product_combo.clear()
        products = get_all_products()
        for product in products:
            label = f"{product['name']} (₦{float(product['price']):,.2f}, Stock: {product['stock_qty']})"
            self.product_combo.addItem(label, product["id"])

    def add_item_to_invoice(self):
        if self.product_combo.count() == 0:
            QMessageBox.warning(self, "No Products", "No products available.")
            return

        qty_text = self.qty_input.text().strip()
        if not qty_text:
            QMessageBox.warning(self, "Missing Quantity", "Enter quantity.")
            return

        try:
            quantity = int(qty_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Quantity", "Quantity must be a whole number.")
            return

        if quantity <= 0:
            QMessageBox.warning(self, "Invalid Quantity", "Quantity must be greater than zero.")
            return

        product_id = self.product_combo.currentData()
        product = get_product_by_id(product_id)

        if not product:
            QMessageBox.warning(self, "Not Found", "Product not found.")
            return

        current_qty_in_cart = 0
        for row_data in self.current_items:
            if row_data["product_id"] == product_id:
                current_qty_in_cart += int(row_data["quantity"])

        if current_qty_in_cart + quantity > int(product["stock_qty"]):
            QMessageBox.warning(
                self,
                "Insufficient Stock",
                f"Only {product['stock_qty']} left for {product['name']}.",
            )
            return

        if product.get("track_serials", False):
            available_serials = product.get("serial_numbers", [])

            if not available_serials:
                QMessageBox.warning(self, "Out of Stock", "No serial numbers available for this product.")
                return

            used_serials = {
                item.get("serial_number")
                for item in self.current_items
                if item["product_id"] == product["id"]
            }

            selectable_serials = [s for s in available_serials if s not in used_serials]

            if not selectable_serials:
                QMessageBox.warning(self, "No Serials", "All serial numbers for this product are already added.")
                return

            used_serials_in_cart = {
                row_data.get("serial_number", "")
                for row_data in self.current_items
                if row_data["product_id"] == product_id and row_data.get("serial_number")
            }

            selectable_serials = [s for s in available_serials if s not in used_serials_in_cart]

            if len(selectable_serials) < quantity:
                QMessageBox.warning(
                    self,
                    "Insufficient Serials",
                    f"Only {len(selectable_serials)} serial number(s) available to add."
                )
                return

            for _ in range(quantity):
                dialog = SerialSelectionDialog(selectable_serials, self)
                if not dialog.exec():
                    return

                selected_serial = dialog.get_selected_serial()

                if not selected_serial:
                    QMessageBox.warning(self, "Missing Serial", "No serial number selected.")
                    return

                self.current_items.append(
                    {
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "price": float(product["price"]),
                        "quantity": 1,
                        "serial_number": selected_serial,
                        "line_total": float(product["price"]),
                    }
                )

                selectable_serials.remove(selected_serial)

        else:
            existing = None
            for row_data in self.current_items:
                if row_data["product_id"] == product["id"] and not row_data.get("serial_number"):
                    existing = row_data
                    break

            if existing:
                existing["quantity"] += quantity
                existing["line_total"] = existing["price"] * existing["quantity"]
            else:
                self.current_items.append(
                    {
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "price": float(product["price"]),
                        "quantity": quantity,
                        "serial_number": "",
                        "line_total": float(product["price"]) * quantity,
                    }
                )

        self.qty_input.clear()
        self.refresh_items_table()

    def refresh_items_table(self):
        self.items_table.setRowCount(0)
        total = 0.0

        for row_index, row_data in enumerate(self.current_items):
            self.items_table.insertRow(row_index)

            serial = row_data.get("serial_number", "")

            values = [
                str(row_data["product_id"]),
                row_data["product_name"],
                serial,
                f"₦{float(row_data['price']):,.2f}",
                str(row_data["quantity"]),
                f"₦{float(row_data['line_total']):,.2f}",
            ]

            for col_index, value in enumerate(values):
                self.items_table.setItem(row_index, col_index, make_table_item(value))

            total += float(row_data["line_total"])

        self.total_label.setText(f"Total: ₦{total:,.2f}")
        self.items_table.resizeColumnsToContents()

    def remove_selected_item(self):
        selected_row = self.items_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Select an item to remove.")
            return

        del self.current_items[selected_row]
        self.refresh_items_table()

    def save_invoice(self):
        if self.customer_combo.count() == 0:
            QMessageBox.warning(self, "No Customers", "Please add a customer first.")
            return

        if not self.current_items:
            QMessageBox.warning(self, "Empty Invoice", "Add at least one item.")
            return

        customer_id = self.customer_combo.currentData()

        try:
            _, invoice_number = create_invoice(customer_id, self.current_items)
            self.current_items = []
            self.refresh_items_table()
            self.load_invoices()
            self.load_products_dropdown()

            QMessageBox.information(
                self,
                "Invoice Saved",
                f"Invoice {invoice_number} saved successfully.",
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def search_serial_usage(self):
        serial = self.serial_search_input.text().strip()

        if not serial:
            QMessageBox.warning(self, "Missing Serial", "Enter a serial number to search.")
            return

        result = find_serial_usage(serial)

        if not result:
            self.serial_search_result.setText(
                f"Serial '{serial}' was not found in sold items or current stock."
            )
            return

        status = result.get("status", "")

        if status == "Sold":
            self.serial_search_result.setText(
                f"Serial: {result['serial_number']}\n"
                f"Product: {result['product_name']}\n"
                f"Status: Sold\n"
                f"Customer: {result['customer_name']}\n"
                f"Invoice: {result['invoice_number']}\n"
                f"Date: {result['created_at']}"
            )
        elif status == "In Stock":
            self.serial_search_result.setText(
                f"Serial: {result['serial_number']}\n"
                f"Product: {result['product_name']}\n"
                f"Status: In Stock"
            )
        else:
            self.serial_search_result.setText(
                f"Serial: {result['serial_number']}\n"
                f"Product: {result['product_name']}"
            )

    def load_invoices(self):
        invoices = get_invoices()
        self.invoice_table.setRowCount(0)

        for row_index, invoice in enumerate(invoices):
            self.invoice_table.insertRow(row_index)

            values = [
                str(invoice["id"]),
                invoice["invoice_number"],
                invoice["customer_name"],
                f"₦{float(invoice['total_amount']):,.2f}",
                invoice["payment_status"],
                invoice["created_at"],
            ]

            for col_index, value in enumerate(values):
                self.invoice_table.setItem(row_index, col_index, make_table_item(value))

        self.invoice_table.resizeColumnsToContents()

    def add_scanned_serial_to_invoice(self):
        serial = self.scan_serial_input.text().strip()

        if not serial:
            QMessageBox.warning(self, "Missing Serial", "Scan or enter a serial number.")
            return

        product = find_product_by_serial(serial)

        if not product:
            usage = find_serial_usage(serial)

            self.serial_search_result.setStyleSheet("color: red; font-weight: bold;")

            if usage and usage.get("status") == "Sold":
                self.serial_search_result.setText(
                    f"Serial '{serial}' was already sold.\n"
                    f"Product: {usage['product_name']}\n"
                    f"Customer: {usage['customer_name']}\n"
                    f"Invoice: {usage['invoice_number']}\n"
                    f"Date: {usage['created_at']}"
                )
            else:
                self.serial_search_result.setText(
                    f"Serial '{serial}' was not found in available stock."
                )

            self.scan_serial_input.selectAll()
            self.scan_serial_input.setFocus()
            return

        for item in self.current_items:
            if item.get("serial_number") == serial:
                self.serial_search_result.setStyleSheet("color: red; font-weight: bold;")
                self.serial_search_result.setText(
                    f"Serial '{serial}' is already added to this invoice."
                )
                self.scan_serial_input.selectAll()
                self.scan_serial_input.setFocus()
                return

        self.current_items.append(
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "price": float(product["price"]),
                "quantity": 1,
                "serial_number": serial,
                "line_total": float(product["price"]),
            }
        )

        index = self.product_combo.findData(product["id"])
        if index >= 0:
            self.product_combo.setCurrentIndex(index)

        self.serial_search_result.setStyleSheet("color: green; font-weight: bold;")
        self.serial_search_result.setText(
            f"Added: {product['name']} | Serial: {serial}"
        )

        self.scan_serial_input.clear()
        self.refresh_items_table()
        self.scan_serial_input.setFocus()

    def open_invoice_details(self, row=None, column=None):
        current_row = self.invoice_table.currentRow()
        if current_row < 0:
            return

        invoice_id = int(self.invoice_table.item(current_row, 0).text())
        invoice = get_invoice_by_id(invoice_id)

        if not invoice:
            QMessageBox.warning(self, "Not Found", "Invoice could not be found.")
            return

        dialog = InvoiceDetailsDialog(invoice, self)
        dialog.exec()


class UsersPage(PageContainer):
    def __init__(self, current_user):
        super().__init__("Users")
        self.current_user = current_user

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by username or role...")
        self.search_input.setObjectName("searchInput")

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("secondaryButton")

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("secondaryButton")

        top_row.addWidget(self.search_input, 1)
        top_row.addWidget(self.search_btn)
        top_row.addWidget(self.clear_btn)

        self.layout.addLayout(top_row)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.add_btn = QPushButton("Add User")
        self.add_btn.setObjectName("primaryButton")

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.setObjectName("secondaryButton")

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("dangerButton")

        actions.addWidget(self.add_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.delete_btn)
        actions.addStretch()

        self.layout.addLayout(actions)

        self.table = QTableWidget(0, 4)
        self.table.setObjectName("productsTable")
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Created At"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setDefaultSectionSize(180)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setWordWrap(False)

        self.layout.addWidget(self.table)

        self.add_btn.clicked.connect(self.open_add_dialog)
        self.edit_btn.clicked.connect(self.edit_selected_user)
        self.delete_btn.clicked.connect(self.delete_selected_user)
        self.search_btn.clicked.connect(self.load_users)
        self.clear_btn.clicked.connect(self.clear_filters)
        self.search_input.returnPressed.connect(self.load_users)

        self.apply_permissions()
        self.load_users()

    def apply_permissions(self):
        is_admin = self.current_user and self.current_user["role"] == "admin"
        self.add_btn.setEnabled(is_admin)
        self.edit_btn.setEnabled(is_admin)
        self.delete_btn.setEnabled(is_admin)

        if not is_admin:
            note = QLabel("Only admin users can manage users.")
            note.setObjectName("pagePlaceholder")
            note.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(note)

    def get_selected_user_id(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return None

        item = self.table.item(selected_row, 0)
        if not item:
            return None

        return int(item.text())

    def load_users(self):
        search_text = self.search_input.text().strip()
        users = get_users(search_text=search_text)
        self.table.setRowCount(0)

        for row_index, user in enumerate(users):
            self.table.insertRow(row_index)

            values = [
                str(user["id"]),
                user["username"],
                user["role"],
                user["created_at"],
            ]

            for col_index, value in enumerate(values):
                self.table.setItem(row_index, col_index, make_table_item(value))

        self.table.resizeColumnsToContents()

    def clear_filters(self):
        self.search_input.clear()
        self.load_users()

    def open_add_dialog(self):
        if not self.current_user or self.current_user["role"] != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can add users.")
            return

        dialog = UserDialog(self)
        if dialog.exec():
            data = dialog.user_data
            try:
                add_user(
                    username=data["username"],
                    password=data["password"],
                    role=data["role"],
                )
                self.load_users()
                QMessageBox.information(self, "Success", "User added successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def edit_selected_user(self):
        if not self.current_user or self.current_user["role"] != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can edit users.")
            return

        user_id = self.get_selected_user_id()
        if user_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a user to edit.")
            return

        user = get_user_by_id(user_id)
        if not user:
            QMessageBox.warning(self, "Not Found", "Selected user could not be found.")
            self.load_users()
            return

        dialog = UserDialog(self, user=user)
        if dialog.exec():
            data = dialog.user_data
            try:
                update_user(
                    user_id=user_id,
                    username=data["username"],
                    password=data["password"],
                    role=data["role"],
                )
                self.load_users()
                QMessageBox.information(self, "Success", "User updated successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def delete_selected_user(self):
        if not self.current_user or self.current_user["role"] != "admin":
            QMessageBox.warning(self, "Access Denied", "Only admin can delete users.")
            return

        user_id = self.get_selected_user_id()
        if user_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a user to delete.")
            return

        if self.current_user["id"] == user_id:
            QMessageBox.warning(self, "Blocked", "You cannot delete your own logged-in account.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this user?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                delete_user(user_id)
                self.load_users()
                QMessageBox.information(self, "Deleted", "User deleted successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))


class ReportsPage(PageContainer):
    def __init__(self, current_user):
        super().__init__("Reports")
        self.current_user = current_user

        role = str((self.current_user or {}).get("role", "")).strip().lower()

        if role != "admin":
            denied = QLabel("Access denied. Only admin can view reports.")
            denied.setObjectName("pagePlaceholder")
            denied.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(denied)
            return

        top_actions = QHBoxLayout()
        top_actions.setSpacing(10)

        self.refresh_btn = QPushButton("Refresh Reports")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.clicked.connect(self.load_reports)

        self.export_sales_btn = QPushButton("Export Sales Report")
        self.export_sales_btn.setObjectName("primaryButton")
        self.export_sales_btn.clicked.connect(self.handle_export_sales_report)

        top_actions.addStretch()
        top_actions.addWidget(self.refresh_btn)
        top_actions.addWidget(self.export_sales_btn)

        self.layout.addLayout(top_actions)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)

        self.total_sales_label = QLabel("Total Sales: ₦0.00")
        self.total_sales_label.setObjectName("sectionTitle")

        self.total_invoices_label = QLabel("Total Invoices: 0")
        self.total_invoices_label.setObjectName("sectionTitle")

        self.paid_sales_label = QLabel("Paid Sales: ₦0.00")
        self.paid_sales_label.setObjectName("sectionTitle")

        self.unpaid_sales_label = QLabel("Unpaid Sales: ₦0.00")
        self.unpaid_sales_label.setObjectName("sectionTitle")

        self.total_sales_label.setMinimumWidth(260)
        self.total_invoices_label.setMinimumWidth(220)
        self.paid_sales_label.setMinimumWidth(240)
        self.unpaid_sales_label.setMinimumWidth(260)

        summary_row.addWidget(self.total_sales_label)
        summary_row.addWidget(self.total_invoices_label)
        summary_row.addWidget(self.paid_sales_label)
        summary_row.addWidget(self.unpaid_sales_label)

        self.layout.addLayout(summary_row)

        inventory_row = QHBoxLayout()
        inventory_row.setSpacing(16)

        self.total_products_label = QLabel("Total Products: 0")
        self.total_products_label.setObjectName("sectionTitle")

        self.total_units_label = QLabel("Stock Units: 0")
        self.total_units_label.setObjectName("sectionTitle")

        self.stock_value_label = QLabel("Stock Value: ₦0.00")
        self.stock_value_label.setObjectName("sectionTitle")

        self.total_products_label.setMinimumWidth(220)
        self.total_units_label.setMinimumWidth(220)
        self.stock_value_label.setMinimumWidth(260)

        inventory_row.addWidget(self.total_products_label)
        inventory_row.addWidget(self.total_units_label)
        inventory_row.addWidget(self.stock_value_label)

        self.layout.addLayout(inventory_row)

        recent_title = QLabel("Recent Sales")
        recent_title.setObjectName("sectionTitle")
        self.layout.addWidget(recent_title)

        self.recent_sales_table = QTableWidget(0, 5)
        self.recent_sales_table.setObjectName("productsTable")
        self.recent_sales_table.setHorizontalHeaderLabels(
            ["Invoice Number", "Customer", "Total", "Status", "Date"]
        )
        self.recent_sales_table.verticalHeader().setVisible(False)
        self.recent_sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recent_sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_sales_table.setFocusPolicy(Qt.NoFocus)
        self.recent_sales_table.setWordWrap(False)
        self.recent_sales_table.setAlternatingRowColors(True)

        recent_header = self.recent_sales_table.horizontalHeader()
        recent_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        recent_header.setSectionResizeMode(1, QHeaderView.Stretch)
        recent_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        recent_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        recent_header.setSectionResizeMode(4, QHeaderView.Stretch)

        self.layout.addWidget(self.recent_sales_table)

        low_stock_title = QLabel("Low Stock Report")
        low_stock_title.setObjectName("sectionTitle")
        self.layout.addWidget(low_stock_title)

        self.low_stock_table = QTableWidget(0, 6)
        self.low_stock_table.setObjectName("productsTable")
        self.low_stock_table.setHorizontalHeaderLabels(
            ["ID", "Product Name", "Category", "Stock Qty", "Status", "Price"]
        )
        self.low_stock_table.verticalHeader().setVisible(False)
        self.low_stock_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.low_stock_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.low_stock_table.setFocusPolicy(Qt.NoFocus)
        self.low_stock_table.setWordWrap(False)
        self.low_stock_table.setAlternatingRowColors(True)

        low_header = self.low_stock_table.horizontalHeader()
        low_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        low_header.setSectionResizeMode(1, QHeaderView.Stretch)
        low_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        low_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        low_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        low_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        self.layout.addWidget(self.low_stock_table)

        self.load_reports()

    def handle_export_sales_report(self):
        try:
            file_path = export_sales_report_to_excel()
            QMessageBox.information(
                self,
                "Export Successful",
                f"Sales report exported successfully.\n\nSaved to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def load_reports(self):
        sales = get_sales_report_summary()
        inventory = get_inventory_report_summary()
        low_stock = get_low_stock_report()
        recent_sales = get_recent_sales_report()

        self.total_sales_label.setText(f"Total Sales: ₦{float(sales['total_sales']):,.2f}")
        self.total_invoices_label.setText(f"Total Invoices: {sales['total_invoices']}")
        self.paid_sales_label.setText(f"Paid Sales: ₦{float(sales['paid_sales']):,.2f}")
        self.unpaid_sales_label.setText(f"Unpaid Sales: ₦{float(sales['unpaid_sales']):,.2f}")

        self.total_products_label.setText(f"Total Products: {inventory['total_products']}")
        self.total_units_label.setText(f"Stock Units: {inventory['total_stock_units']}")
        self.stock_value_label.setText(f"Stock Value: ₦{float(inventory['stock_value']):,.2f}")

        self.load_recent_sales_table(recent_sales)
        self.load_low_stock_table(low_stock)

    def load_recent_sales_table(self, rows):
        self.recent_sales_table.setRowCount(0)

        for row_index, sale in enumerate(rows):
            self.recent_sales_table.insertRow(row_index)

            values = [
                sale["invoice_number"],
                sale["customer_name"],
                f"₦{float(sale['total_amount']):,.2f}",
                sale["payment_status"],
                str(sale["created_at"]),
            ]

            for col_index, value in enumerate(values):
                item = make_table_item(value)

                if col_index == 3:
                    status_value = str(value).upper()
                    if status_value == "PAID":
                        item = make_table_item(value, Qt.darkGreen)
                    elif status_value == "UNPAID":
                        item = make_table_item(value, Qt.red)

                self.recent_sales_table.setItem(row_index, col_index, item)

        self.recent_sales_table.resizeRowsToContents()

    def load_low_stock_table(self, rows):
        self.low_stock_table.setRowCount(0)

        for row_index, product in enumerate(rows):
            self.low_stock_table.insertRow(row_index)

            values = [
                str(product["id"]),
                product["name"],
                product["category"],
                str(product["stock_qty"]),
                product["status"],
                f"₦{float(product['price']):,.2f}",
            ]

            for col_index, value in enumerate(values):
                if col_index == 4:
                    status_value = str(value).lower()
                    if status_value == "low stock":
                        item = make_table_item(value, Qt.darkYellow)
                    elif status_value == "out of stock":
                        item = make_table_item(value, Qt.red)
                    else:
                        item = make_table_item(value)
                else:
                    item = make_table_item(value)

                self.low_stock_table.setItem(row_index, col_index, item)

        self.low_stock_table.resizeRowsToContents()