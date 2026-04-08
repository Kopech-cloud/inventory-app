import os
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from database.db import create_default_admin, init_db
from ui.login import LoginWindow


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    init_db()
    create_default_admin()

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/icon.png")))

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()