from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor
import pyqtgraph as pqg
from VolumeViewModel import *
import pyvista as pv

#Mettere i pulsanti per l'import del file, che si colleghino ad update_volumes
#Qui andrà imread

def create_titled_view(title_text, grid, col_grid, row_grid):
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(2, 2 ,2, 2)

    #qui si inizializza l'etichetta del titolo, con tanto di STILE
    tit_lbl = QLabel(title_text)
    tit_lbl.setStyleSheet("background-color: #333; color: white; font-weight: bold; padding: 4px;")
    tit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(tit_lbl)

    btn_layout = QHBoxLayout()
    left_rot_btn = QPushButton("Ruota 90° sx")
    right_rot_btn = QPushButton("Ruota 90° dx")
    btn_layout.addWidget(left_rot_btn)
    btn_layout.addWidget(right_rot_btn)
    layout.addLayout(btn_layout)

    view = pqg.ImageView()
    view.ui.roiBtn.hide()
    view.ui.menuBtn.hide()
    layout.addWidget(view)

    grid.addWidget(container, row_grid, col_grid)

    return view, left_rot_btn, right_rot_btn

class VolumeView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = VolumeViewModel()
        self.dimVoxel = (0.5, 0.5, 0.5)
        """
        PRESETTING per rendere scorrevoli le finestre
        """
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)#larghezza adattabile

        # contenitore generale, consente di "simulare una pagina web scorrevole"
        self.main_content_scrollable_widget = QWidget()
        self.main_content_scrollable_widget.setMinimumHeight(1000)

        """ Qui sotto sta il layout principale """
        self.main_layout = QVBoxLayout(self.main_content_scrollable_widget)#anche questa è una scatola vuota

        self.scroll_area.setWidget(self.main_content_scrollable_widget)

        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(self.scroll_area)

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
        """
        self.view_sliceX = pqg.ImageView()
        self.grid.addWidget(self.view_sliceX, 0, 1)

        self.view_sliceY = pqg.ImageView()
        self.grid.addWidget(self.view_sliceY, 1, 0)

        self.view_sliceZ = pqg.ImageView()
        self.grid.addWidget(self.view_sliceZ, 1, 1)
        """

        self.view_sliceX, self.btn_X_left, self.btn_X_right = create_titled_view("Vista Asse X (Sagittale)", self.grid, 0, 1)
        self.view_sliceY, self.btn_Y_left, self.btn_Y_right = create_titled_view("Vista Asse Y (Coronale)", self.grid, 1, 0)
        self.view_sliceZ, self.btn_Z_left, self.btn_Z_right = create_titled_view("Vista Asse Z (Assiale)", self.grid, 1, 1)

        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        #FOR per nascondere i menù superflui
        for view in [self.view_sliceX, self.view_sliceY, self.view_sliceZ]:
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()

        """
        UNWRAPPING
        """
        self.unwrapping_btn = QPushButton("Unwrap Faces")
        self.unwrapping_btn.setEnabled(False)
        self.main_layout.addWidget(self.unwrapping_btn)

        self.unwrapContainer = QWidget()#il contenitore delle 4
        self.unwrapContainer.setMinimumHeight(300)
        self.unwrap_layout = QHBoxLayout(self.unwrapContainer)
        self.unwrap_layout.setContentsMargins(0,0,0,0)
        self.unwrapped_views = []
        for _ in range(4):
            this_view = pqg.ImageView()
            this_view.ui.roiBtn.hide()
            this_view.ui.menuBtn.hide()
            self.unwrap_layout.addWidget(this_view)
            self.unwrapped_views.append(this_view)

        self.main_layout.addWidget(self.unwrapContainer)
        self.unwrapContainer.hide()#per nasconderlo all'avvio

        """
        CONNESSIONI
        """
        self.import_btn.clicked.connect(self._open_file_dialog)
        self.vm.volume_loaded.connect(self._setGridImage)

        self.btn_X_left.clicked.connect(lambda: self._rotate_view(self.view_sliceX, -90))
        self.btn_X_right.clicked.connect(lambda: self._rotate_view(self.view_sliceX, 90))
        
        self.btn_Y_left.clicked.connect(lambda: self._rotate_view(self.view_sliceY, -90))
        self.btn_Y_right.clicked.connect(lambda: self._rotate_view(self.view_sliceY, 90))
        
        self.btn_Z_left.clicked.connect(lambda: self._rotate_view(self.view_sliceZ, -90))
        self.btn_Z_right.clicked.connect(lambda: self._rotate_view(self.view_sliceZ, 90))

        self.unwrapping_btn.clicked.connect(self.vm.unwrap_current_volume)
        self.vm.volume_unwrapped.connect(self._show_unwrapped_image)

        self.vm.error_occurred.connect(self._show_popup_error_occurred)

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 
                                                   "Select .tiff volume", 
                                                   "",
                                                   ".tiff images (*.tiff *.tif)")#il _ è perché la funzione _open_file_dialog di base restituisce una tupla di 2 elementi
        if file_path:
            self.vm.load_tiff(file_path)#funzione nel ViewModel

    def _setGridImage(self, tiff_volume_array : object): #questa funzione si occupera di proiettare le sezioni dell'immagine .tiff in tutte le sue prospettive-
        self.unwrapContainer.hide()
        #Settaggio del 2D
        import numpy as np
        
        self.view_sliceX.setImage(tiff_volume_array) #letteralmente un setter
        self.view_sliceY.setImage(np.transpose(tiff_volume_array, (1, 0, 2)))
        self.view_sliceZ.setImage(np.transpose(tiff_volume_array, (2, 0, 1)))

        """
        self.view_sliceX.getView().invertX(True)
        self.view_sliceX.getImageItem().setRotation(90)
        """

        #Settaggio del 3D
        self.view_3d.clear()
        self.view_3d.set_background("black")

        #FIXME: momentaneamente disattivato poiché non funzionante/non testabile
        """
        render3D = pv.ImageData()
        # Nota: Numpy ordina gli assi (Z, Y, X), mentre PyVista usa (X, Y, Z). 
        # Invertiamo le dimensioni per evitare crash o geometrie distorte
        render3D.dimensions = tiff_volume_array.shape[::-1]
        render3D.spacing = self.dimVoxel

        render3D.point_data["values"] = tiff_volume_array.flatten(order = "F")#il valore di ogni cella del render3D verrà equiparato al rispettivo della matrice 3D
        self.view_3d.add_volume(render3D, cmap = "bone", opacity = "linear") # comando che crea l'area 3D interagibile come vogliamo noi

        self.view_3d.reset_camera()#per centrare la camera sul pezzo di legno
        self.view_3d.update()#forza il refresh visivo
        """
        self.unwrapping_btn.setEnabled(True)

    def _rotate_view(self, rotating_view, degrees):
        item = rotating_view.getImageItem()
        current_rotation = item.rotation()
        item.setRotation((current_rotation + degrees) % 360)

    def _show_popup_error_occurred(self, msg: str):
        QMessageBox.critical(self, "Errore", msg)

    def _show_unwrapped_image(self, faces_list: list):
        self.unwrapContainer.show()
        for i, face_array in enumerate(faces_list):
            #autoRange serve per orientare correttamente le proiezioni lungo l'asse Z
            self.unwrapped_views[i].setImage(face_array, autoRange = True)#sono quattro spazi vuoti che vengono riempiti proprio come accade al momento del caricamento del file