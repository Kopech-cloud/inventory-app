from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.db import authenticate_user
from ui.dashboard import DashboardWindow

import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Kopech Solutions Inventory")
        self.resize(900, 560)
        self.setMinimumSize(820, 520)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left_panel = self.build_left_panel()
        right_panel = self.build_right_panel()

        root.addWidget(left_panel, 1)
        root.addWidget(right_panel, 1)

        self.apply_styles()

    def build_left_panel(self):
        frame = QFrame()
        frame.setObjectName("leftPanel")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        pixmap = QPixmap(resource_path("assets/logo.png"))
        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaled(220, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("Kopech Inventory")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(
            "Inventory, customers, invoicing, and reporting in one desktop app."
        )
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        return frame

    def build_right_panel(self):
        frame = QFrame()
        frame.setObjectName("rightPanel")

        outer = QVBoxLayout(frame)
        outer.setContentsMargins(70, 50, 70, 50)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(16)

        heading = QLabel("Sign in")
        heading.setObjectName("loginHeading")

        subheading = QLabel("Use your account to access the system.")
        subheading.setObjectName("loginSubheading")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setObjectName("loginInput")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("loginInput")

        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("loginButton")

       

        card_layout.addWidget(heading)
        card_layout.addWidget(subheading)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.login_btn)
       

        outer.addWidget(card)

        self.login_btn.clicked.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.returnPressed.connect(self.handle_login)

        return frame

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing Info", "Enter username and password.")
            return

        user = authenticate_user(username, password)
        if not user:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            return

        self.dashboard = DashboardWindow(user)
        self.dashboard.show()
        self.close()

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f7fb;
            }

            #leftPanel {
                background: #111827;
            }

            #rightPanel {
                background: #f5f7fb;
            }

            #welcomeTitle {
                color: white;
                font-size: 30px;
                font-weight: 700;
            }

            #welcomeSubtitle {
                color: #d1d5db;
                font-size: 15px;
                line-height: 1.4;
            }

            #loginCard {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 18px;
                min-width: 360px;
                max-width: 420px;
            }

            #loginHeading {
                color: #111827;
                font-size: 28px;
                font-weight: 700;
            }

            #loginSubheading {
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 6px;
            }

            QLineEdit#loginInput {
                background: white;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 14px;
                min-height: 22px;
            }

            QLineEdit#loginInput:focus {
                border: 1px solid #10b981;
            }

            QPushButton#loginButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#loginButton:hover {
                background: #0ea371;
            }

            #loginHint {
                color: #6b7280;
                font-size: 12px;
                margin-top: 4px;
            }
        """)