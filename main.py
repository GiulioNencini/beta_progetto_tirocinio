import sys
from PySide6.QtWidgets import QApplication
from MainView import MainView

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainView()
    window.resize(1000, 800)
    window.setWindowTitle("Render3D and slices")
    window.show()

    sys.exit(app.exec())

