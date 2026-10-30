from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from pyvistaqt import QtInteractor
import pyqtgraph as pqg
from VolumeViewModel import *
import pyvista as pv

#Mettere i pulsanti per l'import del file, che si colleghino ad update_volumes
#Qui andrà imread

class VolumeView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = VolumeViewModel()
        self.dimVoxel = (0.5, 0.5, 0.5)

        # Qui sotto sta il layout principale
        self.main_layout = QVBoxLayout(self)#anche questa è una scatola vuota

        self.import_btn = QPushButton("Import .tiff")
        self.main_layout.addWidget(self.import_btn)

        # la griglia di layout
        self.grid = QGridLayout()# a questo oggetto si possono aggiungere widget, di per sé è vuoto
        self.main_layout.addLayout(self.grid)

        # 2 Il widget per il 3D
        self.view_3d = QtInteractor(self)
        self.grid.addWidget(self.view_3d, 0, 0) #il widget per il 3d viene prima creato e poi aggiunto alla griglia in posizione (0,0)

        # Gli widget delle proiezioni 2D, stesso discorso: prima sono creati e poi sono aggiunti alla griglia
        # Queste ImageView sono tuttavia ancora vuote, verranno riempite solo al momento del caricamento del file .tiff (vedi funzione sotto)
        self.view_sliceX = pqg.ImageView()
        self.grid.addWidget(self.view_sliceX, 0, 1)

        self.view_sliceY = pqg.ImageView()
        self.grid.addWidget(self.view_sliceY, 1, 0)

        self.view_sliceZ = pqg.ImageView()
        self.grid.addWidget(self.view_sliceZ, 1, 1)


        #FOR per nascondere i menù superflui
        for view in [self.view_sliceX, self.view_sliceY, self.view_sliceZ]:
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()
        """
        CONNESSIONI
        """
        self.import_btn.clicked.connect(self._open_file_dialog)
        self.vm.volume_loaded.connect(self.setGridImage)
        self.vm.error_occurred.connect(self.show_popup_error_occurred)#FIXME cosa ci metto per l'errore?

    
    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 
                                                   "Select .tiff volume", 
                                                   "",
                                                   ".tiff images (*.tiff *.tif)")#il _ è perché la funzione _open_file_dialog di base restituisce una tupla di 2 elementi
        if file_path:
            self.vm.load_tiff(file_path)#funzione nel ViewModel

    
    def setGridImage(self, tiff_volume_array : object): #questa funzione si occupera di proiettare le sezioni dell'immagine .tiff in tutte le sue prospettive
        import numpy as np
        self.view_sliceX.setImage(tiff_volume_array) #letteralmente un setter
        self.view_sliceY.setImage(np.transpose(tiff_volume_array, (1, 0, 2)))
        self.view_sliceZ.setImage(np.transpose(tiff_volume_array, (2, 0, 1)))

        render3D = pv.ImageData()
        render3D.tiff_volume_array.shape
        render3D.spacing = self.dimVoxel

        render3D.point_data["values"] = tiff_volume_array.flatten(order = "F")#il valore di ogni cella del render3D verrà equiparato al rispettivo della matrice 3D
        self.view_3d.add_volume(render3D, cmap = "bone") # comando che crea l'area 3D interagibile come vogliamo noi

    def show_popup_error_occurred(self, msg: str):
        QMessageBox.critical(self, "Errore", msg)
    