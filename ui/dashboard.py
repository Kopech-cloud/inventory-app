from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from database.db import (
    get_total_products,
    get_low_stock_products_count,
    get_total_customers,
    get_total_invoices,
    get_total_sales,
    get_recent_invoices,
    get_low_stock_products,
)

from ui.pages import (
    CustomersPage,
    InvoicesPage,
    ProductsPage,
    ReportsPage,
    UsersPage,
)


class SummaryCard(QFrame):
    def __init__(self, number: str, title: str, subtitle: str, color: str):
        super().__init__()
        self.setObjectName("summaryCard")
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        number_label = QLabel(number)
        number_label.setObjectName("cardNumber")
        number_label.setStyleSheet(f"color: {color};")

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("cardSubtitle")

        layout.addWidget(number_label)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addStretch()


class InfoPanel(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("infoPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")

        placeholder = QLabel("Content will go here")
        placeholder.setObjectName("panelPlaceholder")
        placeholder.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(placeholder, 1)


class SidebarButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(44)
        self.setObjectName("sidebarButton")
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_active(self, active: bool):
        self.setChecked(active)
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class DashboardHomePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        header = QLabel("Dashboard")
        header.setObjectName("pageTitle")
        layout.addWidget(header)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        total_products = get_total_products()
        low_stock_count = get_low_stock_products_count()
        total_customers = get_total_customers()
        total_invoices = get_total_invoices()
        total_sales = get_total_sales()

        cards = [
            SummaryCard(str(total_products), "Products", "TOTAL PRODUCTS", "#34a4eb"),
            SummaryCard(str(low_stock_count), "Items", "LOW STOCK", "#f59e0b"),
            SummaryCard(str(total_customers), "Customers", "TOTAL CUSTOMERS", "#10b981"),
            SummaryCard(str(total_invoices), "Invoices", "TOTAL INVOICES", "#8b5cf6"),
            SummaryCard(f"₦{total_sales:,.0f}", "Sales", "TOTAL SALES", "#ef4444"),
        ]

        for card in cards:
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        row_two = QGridLayout()
        row_two.setHorizontalSpacing(16)
        row_two.setVerticalSpacing(16)

        recent_panel = QFrame()
        recent_panel.setObjectName("infoPanel")
        recent_layout = QVBoxLayout(recent_panel)
        recent_layout.setContentsMargins(20, 16, 20, 16)
        recent_layout.setSpacing(12)

        recent_title = QLabel("RECENT INVOICES")
        recent_title.setObjectName("panelTitle")
        recent_layout.addWidget(recent_title)

        recent_invoices = get_recent_invoices()
        if recent_invoices:
            for invoice in recent_invoices:
                line = QLabel(
                    f"{invoice['invoice_number']}  •  {invoice['customer_name']}  •  ₦{float(invoice['total_amount']):,.2f}"
                )
                line.setObjectName("dashboardLine")
                recent_layout.addWidget(line)
        else:
            empty = QLabel("No invoices yet.")
            empty.setObjectName("panelPlaceholder")
            empty.setAlignment(Qt.AlignCenter)
            recent_layout.addWidget(empty)

        low_stock_panel = QFrame()
        low_stock_panel.setObjectName("infoPanel")
        low_stock_layout = QVBoxLayout(low_stock_panel)
        low_stock_layout.setContentsMargins(20, 16, 20, 16)
        low_stock_layout.setSpacing(12)

        low_stock_title = QLabel("LOW STOCK ITEMS")
        low_stock_title.setObjectName("panelTitle")
        low_stock_layout.addWidget(low_stock_title)

        low_stock_items = get_low_stock_products()
        if low_stock_items:
            for product in low_stock_items:
                line = QLabel(
                    f"{product['name']}  •  {product['category']}  •  Qty: {product['stock_qty']}"
                )
                line.setObjectName("dashboardLine")
                low_stock_layout.addWidget(line)
        else:
            empty = QLabel("No low stock items.")
            empty.setObjectName("panelPlaceholder")
            empty.setAlignment(Qt.AlignCenter)
            low_stock_layout.addWidget(empty)

        summary_panel = QFrame()
        summary_panel.setObjectName("infoPanel")
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setContentsMargins(20, 16, 20, 16)
        summary_layout.setSpacing(12)

        summary_title = QLabel("BUSINESS SUMMARY")
        summary_title.setObjectName("panelTitle")
        summary_layout.addWidget(summary_title)

        summary_lines = [
            f"Products in system: {total_products}",
            f"Customers registered: {total_customers}",
            f"Invoices created: {total_invoices}",
            f"Low stock alerts: {low_stock_count}",
            f"Total sales value: ₦{total_sales:,.2f}",
        ]

        for text in summary_lines:
            line = QLabel(text)
            line.setObjectName("dashboardLine")
            summary_layout.addWidget(line)

        summary_layout.addStretch()

        row_two.addWidget(recent_panel, 0, 0)
        row_two.addWidget(low_stock_panel, 0, 1)
        row_two.addWidget(summary_panel, 0, 2)

        row_two.setColumnStretch(0, 2)
        row_two.setColumnStretch(1, 2)
        row_two.setColumnStretch(2, 1)

        layout.addLayout(row_two)
        layout.addStretch()

class DashboardWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = dict(user) if user else {}
        self.role = (self.user.get("role") or "").strip().lower()
        self.setWindowTitle("Kopech Solutions Limited - Inventory App")
        self.resize(1450, 900)

        self.sidebar_buttons = {}
        self.allowed_pages = self.get_allowed_pages()


        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self.create_sidebar())
        root_layout.addWidget(self.create_main_content(), 1)

        self.apply_styles()
        self.switch_page("Dashboard")

    def get_allowed_pages(self):
        if self.role == "admin":
            return ["Dashboard", "Products", "Customers", "Invoices", "Users", "Reports"]

        if self.role == "staff":
            return ["Dashboard", "Products", "Customers", "Invoices"]

        return ["Dashboard"]

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)

        logo = QLabel()
        pixmap = QPixmap("assets/logo.png")
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(180, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        layout.addSpacing(10)

        for name in self.allowed_pages:
            btn = SidebarButton(name)
            btn.clicked.connect(lambda checked=False, n=name: self.switch_page(n))
            layout.addWidget(btn)
            self.sidebar_buttons[name] = btn

        layout.addStretch()

        user_card = QFrame()
        user_card.setObjectName("userCard")
        user_layout = QVBoxLayout(user_card)
        user_layout.setContentsMargins(12, 12, 12, 12)
        user_layout.setSpacing(4)

        username = self.user["username"] if self.user and "username" in self.user.keys() else "Unknown"
        role = self.user["role"] if self.user and "role" in self.user.keys() else "user"

        self.user_name_label = QLabel(username)
        self.user_name_label.setObjectName("userNameLabel")

        self.user_role_label = QLabel(role.title())
        self.user_role_label.setObjectName("userRoleLabel")

        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setObjectName("logoutButton")
        self.logout_btn.clicked.connect(self.handle_logout)

        user_layout.addWidget(self.user_name_label)
        user_layout.addWidget(self.user_role_label)
        user_layout.addSpacing(8)
        user_layout.addWidget(self.logout_btn)

        layout.addWidget(user_card)

        footer = QLabel("v2.0")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        return sidebar

    def create_main_content(self):
        container = QWidget()
        container.setObjectName("mainContent")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        self.stacked = QStackedWidget()
        self.stacked.setObjectName("stackedPages")

        # only track allowed page names for permissions
        self.pages = {}

        layout.addWidget(self.stacked)
        return container


    def build_page(self, name: str):
        if name == "Dashboard":
            return DashboardHomePage()
        elif name == "Products":
            return ProductsPage(self.user)
        elif name == "Customers":
            return CustomersPage(self.user)
        elif name == "Invoices":
            return InvoicesPage(self.user)
        elif name == "Users":
            return UsersPage(self.user)
        elif name == "Reports":
            return ReportsPage(self.user)
        return None


    def switch_page(self, name: str):
        if name not in self.allowed_pages:
            QMessageBox.warning(self, "Access Denied", "You do not have permission to open this page.")
            return

        if name == "Dashboard":
            if "Dashboard" in self.pages:
                old_page = self.pages["Dashboard"]
                self.stacked.removeWidget(old_page)
                old_page.deleteLater()
                del self.pages["Dashboard"]

            page = self.build_page("Dashboard")
            self.pages["Dashboard"] = page
            self.stacked.addWidget(page)
            self.stacked.setCurrentWidget(page)

        else:
            if name not in self.pages:
                page = self.build_page(name)
                if page is None:
                    QMessageBox.warning(self, "Error", f"Could not load page: {name}")
                    return

                self.pages[name] = page
                self.stacked.addWidget(page)

            self.stacked.setCurrentWidget(self.pages[name])

        for page_name, btn in self.sidebar_buttons.items():
            btn.set_active(page_name == name)

    def handle_logout(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Logout")
        msg.setText("Are you sure you want to logout?")
        msg.setIcon(QMessageBox.Question)

        yes_btn = msg.addButton("Yes", QMessageBox.YesRole)
        no_btn = msg.addButton("No", QMessageBox.NoRole)

        msg.setDefaultButton(no_btn)

        msg.setStyleSheet("""
            QMessageBox {
                background: white;
            }

            QMessageBox QLabel {
                color: #111827;
                font-size: 14px;
            }

            QPushButton {
                min-width: 90px;
                min-height: 34px;
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton[text="Yes"] {
                background: #ef4444;
                color: white;
                border: none;
            }

            QPushButton[text="Yes"]:hover {
                background: #dc2626;
            }

            QPushButton[text="No"] {
                background: white;
                color: #374151;
                border: 1px solid #d1d5db;
            }

            QPushButton[text="No"]:hover {
                background: #f3f4f6;
            }
        """)

        msg.exec()

        if msg.clickedButton() == yes_btn:
            from ui.login import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f7fb;
            }

            QDialog {
                background: #ffffff;
                color: #111827;
            }

            QLabel {
                color: #111827;
            }

            #sidebar {
                background: #1f2937;
            }

            #sidebarFooter {
                color: #9ca3af;
                font-size: 12px;
                padding: 8px 10px;
            }

            QPushButton#sidebarButton {
                text-align: left;
                padding: 12px 14px;
                border: none;
                border-radius: 10px;
                background: transparent;
                color: #e5e7eb;
                font-size: 15px;
                font-weight: 600;
            }

            QPushButton#sidebarButton:hover {
                background: #2b3647;
            }

            QPushButton#sidebarButton[active="true"] {
                background: #10b981;
                color: white;
            }

            #userCard {
                background: #111827;
                border: 1px solid #374151;
                border-radius: 14px;
            }

            #userNameLabel {
                color: white;
                font-size: 15px;
                font-weight: 700;
            }

            #userRoleLabel {
                color: #9ca3af;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#logoutButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton#logoutButton:hover {
                background: #dc2626;
            }

            #mainContent {
                background: #f5f7fb;
            }

            #pageTitle, #sectionTitle {
                font-size: 28px;
                font-weight: 700;
                color: #111827;
                padding-bottom: 4px;
            }

            #summaryCard, #pageContainer, #miniCard {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
            }

            #cardNumber {
                font-size: 36px;
                font-weight: 700;
            }

            #cardTitle {
                font-size: 18px;
                font-weight: 600;
                color: #374151;
            }

            #cardSubtitle {
                font-size: 13px;
                font-weight: 700;
                color: #6b7280;
            }

            #infoPanel {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
                min-height: 220px;
            }

            #panelTitle {
                font-size: 18px;
                font-weight: 700;
                color: #1f2937;
            }

            #panelPlaceholder, #pagePlaceholder {
                font-size: 15px;
                color: #9ca3af;
                border: 2px dashed #d1d5db;
                border-radius: 12px;
                background: #f9fafb;
                min-height: 120px;
                padding: 20px;
            }

            #miniCardNumber {
                font-size: 26px;
                font-weight: 700;
                color: #111827;
            }

            #miniCardLabel {
                font-size: 14px;
                color: #6b7280;
                font-weight: 600;
            }

            QPushButton#primaryButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#primaryButton:hover {
                background: #0ea371;
            }

            QPushButton#secondaryButton {
                background: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#secondaryButton:hover {
                background: #f3f4f6;
            }

            QPushButton#dangerButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#dangerButton:hover {
                background: #dc2626;
            }

            QLineEdit#searchInput {
                background: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 14px;
            }

            QLineEdit#searchInput:focus {
                border: 1px solid #10b981;
            }

            QLineEdit {
                color: #111827;
                background: white;
            }

            QComboBox#statusFilter {
                background: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 10px 12px;
                font-size: 14px;
                min-width: 140px;
            }

            QComboBox#statusFilter:focus {
                border: 1px solid #10b981;
            }

            QComboBox QAbstractItemView {
                background: white;
                color: #111827;
                selection-background-color: #dbeafe;
                selection-color: #111827;
                border: 1px solid #d1d5db;
            }

            QTextEdit {
                background: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 8px;
                font-size: 14px;
            }

            QTextEdit:focus {
                border: 1px solid #10b981;
            }

            QTableWidget#productsTable {
                background: white;
                color: #111827;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                gridline-color: #e5e7eb;
                font-size: 14px;
                selection-background-color: #dbeafe;
                selection-color: #111827;
            }

            QHeaderView::section {
                background: #f9fafb;
                color: #374151;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #e5e7eb;
                font-weight: 700;
            }

            QTableWidget::item {
                color: #111827;
                padding: 8px;
            }

            QTableWidget::item:selected {
                background: #dbeafe;
                color: #111827;
            }

            QMessageBox QPushButton {
                min-width: 90px;
                min-height: 34px;
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 700;
                background: white;
                color: #111827;
                border: 1px solid #d1d5db;
            }

            QMessageBox QPushButton:hover {
                background: #f3f4f6;
            }
                    """)