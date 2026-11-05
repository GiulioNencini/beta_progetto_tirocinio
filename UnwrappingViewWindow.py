from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
import pyqtgraph as pqg

"""
DOVE SI VISUALIZZATO I RISULTATI DELL'UNWRAPPING, è una vista che appare in una finestra separata
"""

class UnwrappingViewWindow(QWidget):
    def __init__(self, faces_list):
        super().__init__()
        self.setWindowTitle("Facce unwrappate")
        self.resize(600, 900)

        #rendiamola scrollabile
        scroll_unw = QScrollArea(self)
        scroll_unw.setWidgetResizable(True)
        content_widget = QWidget()
        layout_unw = QVBoxLayout(content_widget)

        names = ["Faccia 1", "Faccia 2", "Faccia 3", "Faccia 4"]

        for i, face_array in enumerate(faces_list):
            names_lbl = QLabel(names[i])
            names_lbl.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #333; color: white; padding: 5px;")
            names_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_unw.addWidget(names_lbl)

            view = pqg.ImageView()
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()

            #view.getView().setMouseEnabled(x = False, y = False)
            view.setMinimumHeight(250)
            view.setImage(face_array, autoRange = True)
            layout_unw.addWidget(view)

        scroll_unw.setWidget(content_widget)

        #creaiamo ora il layout principale della nuova finestra
        win_layout = QVBoxLayout(self)
        win_layout.setContentsMargins(0, 0, 0, 0,)
        win_layout.addWidget(scroll_unw)