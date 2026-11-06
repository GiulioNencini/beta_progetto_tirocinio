from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
import pyqtgraph as pqg
import numpy as np
from MainViewModel import MainViewModel

"""
DOVE SI VISUALIZZANO I RISULTATI DELL'UNWRAPPING, è una vista che appare in una finestra separata
"""

class UnwrappingViewWindow(QWidget):
    def __init__(self, faces_list, view_model : MainViewModel):
        super().__init__()
        self.setWindowTitle("Facce unwrappate")
        self.resize(1100, 900)
        self.vm = view_model

        main_uw_layout = QHBoxLayout(self)

        #Creiamo la colonna di sinistra per le 4 immagini unwrappate (scrollabile a sé)
        scroll_unw_left = QScrollArea(self)
        scroll_unw_left.setWidgetResizable(True)
        content_left = QWidget()
        layout_unw_left = QVBoxLayout(content_left)

        names = ["Faccia 1", "Faccia 2", "Faccia 3", "Faccia 4"]

        for i, face_array in enumerate(faces_list):
            names_lbl = QLabel(names[i])
            names_lbl.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #333; color: white; padding: 5px;")
            names_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_unw_left.addWidget(names_lbl)

            view = pqg.ImageView()
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()
            view.setMinimumHeight(200)

            view.getView().invertY(True)

            view.setImage(face_array, autoRange = True)
            layout_unw_left.addWidget(view)

        scroll_unw_left.setWidget(content_left)
        main_uw_layout.addWidget(scroll_unw_left, stretch = 1)

        #Creiamo adesso la colonna di destra che avrà la vista con le immagini unite, nonché il pulsante di export
        content_right = QWidget()
        layout_unw_right = QVBoxLayout(content_right)

        lbl_right = QLabel("Vista delle 4 facce")
        lbl_right.setStyleSheet("font-weight: bold; font-size: 16px; background-color: #0055ff; color: white; padding: 10px;")
        lbl_right.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_unw_right.addWidget(lbl_right)

        #creiamo concretamente la quinta vista
        self.right_view = pqg.ImageView()
        self.right_view.ui.roiBtn.hide()
        self.right_view.ui.menuBtn.hide()

        self.right_view.getView().invertY(True)

        #adesso dobbiamo concatenare le 4 facce, la concatenazione avviene lungo l'asse 1 poiché l'asse 0 è uguale per tutti
        self.combined_faces = np.concatenate(faces_list, axis = 1)
        self.right_view.setImage(self.combined_faces, autoRange = True)
        layout_unw_right.addWidget(self.right_view)

        #pulsante di export dell'immagine concatenata
        self.btn_export = QPushButton("Esporta facce concatenate")
        self.btn_export.setStyleSheet("padding: 12px; font-weight: bold; font-size: 14px; background-color: #28a745; color: white;")
        self.btn_export.clicked.connect(self._save_unwrapped_image)
        self.vm.unwrapped_saved.connect(self._show_exporting_success)
        self.vm.error_occurred.connect(self._show_exporting_fail)
        layout_unw_right.addWidget(self.btn_export)

        main_uw_layout.addWidget(content_right, stretch = 1)
        main_uw_layout.setContentsMargins(0, 0, 0, 0,)

    def _save_unwrapped_image(self):
        # QFileDialog per scegliere dove salvare
        file_path, _ = QFileDialog.getSaveFileName(self, 
                                                   "Salva Composizione", 
                                                   "", 
                                                   "PNG Files (*.png);;JPEG Files (*.jpg);;TIFF Files (*.tiff)")
        if file_path:
            self.vm._export_unwrapped_image(file_path, self.right_view)

    def _show_exporting_success(self, msg : str):
        QMessageBox.information(self, "Successo!", msg)

    def _show_exporting_fail(self, msg : str):
        QMessageBox.critical(self, "Errore!", msg)