import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from database.db_sqlite_backup import create_default_admin, init_db
from ui.login import LoginWindow


def main():
    init_db()
    create_default_admin()

    app = QApplication(sys.argv)

    # set application icon
    app.setWindowIcon(QIcon("assets/icon.png"))

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()