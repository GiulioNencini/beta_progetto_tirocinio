import sys
from PySide6.QtWidgets import QApplication
from VolumeView import *

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = VolumeView()
    window.resize(1000, 800)
    window.setWindowTitle("Render3D and slices")
    window.show()

    sys.exit(app.exec())

