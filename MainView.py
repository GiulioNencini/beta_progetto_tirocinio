from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor
import pyqtgraph as pqg
from MainViewModel import *
from ROIManager import ROIManager
from UnwrappingViewWindow import UnwrappingViewWindow
import pyvista as pv

def create_titled_view(title_text, grid, col_in_grid, row_in_grid):
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(3, 3 ,3, 3)

    #qui si inizializza l'etichetta del titolo, con tanto di STILE
    tit_lbl = QLabel(title_text)
    tit_lbl.setStyleSheet("background-color: #333; color: white; font-weight: bold; padding: 4px;")
    tit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(tit_lbl)

    layout_of_btns = QHBoxLayout()

    center_image_btn = QPushButton("Centra l'immagine")
    center_image_btn.setEnabled(False)
    layout_of_btns.addWidget(center_image_btn)
    left_rot_btn = QPushButton("Ruota 90° sx")
    right_rot_btn = QPushButton("Ruota 90° dx")
    left_rot_btn.setEnabled(False)
    right_rot_btn.setEnabled(False)
    layout_of_btns.addWidget(left_rot_btn)
    layout_of_btns.addWidget(right_rot_btn)

    layout.addLayout(layout_of_btns)
    # Gli widget delle proiezioni 2D, stesso discorso: prima sono creati e poi sono aggiunti alla griglia
    # Queste ImageView sono tuttavia ancora vuote, verranno riempite solo al momento del caricamento del file .tiff
    view = pqg.ImageView()
    view.ui.roiBtn.hide()
    view.ui.menuBtn.hide()
    layout.addWidget(view)

    grid.addWidget(container, row_in_grid, col_in_grid)

    return view, center_image_btn, left_rot_btn, right_rot_btn

class MainView(QWidget):
    def __init__(self):
        super().__init__()
        self.vm = VolumeViewModel()
        self.dimVoxel = (0.5, 0.5, 0.5)

        """
        PRESETTING per rendere scorrevoli le finestre e far apparire tutte le viste e pulsanti
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

        self.view_sliceZ, self.btn_center_imageZ, self.btn_Z_rot_left, self.btn_Z_rot_right = create_titled_view("Vista Asse Z (Assiale)", self.grid, 1, 0)
        self.view_sliceX, self.btn_center_imageX, self.btn_X_rot_left, self.btn_X_rot_right = create_titled_view("Vista Asse X (Sagittale)", self.grid, 1, 1)
        self.view_sliceY, self.btn_center_imageY, self.btn_Y_rot_left, self.btn_Y_rot_right = create_titled_view("Vista Asse Y (Coronale)", self.grid, 0, 1)

        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        #FOR per nascondere i menù superflui
        for view in [self.view_sliceX, self.view_sliceY, self.view_sliceZ]:
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()


        #inizializiamo il pulsante per attivare/disattivare le linee
        #quindi attivare o disattivare la selezione delle coordinate per l'unwrapping
        self.btn_toggle_roi = QPushButton("Attiva Mirino (ROI)")
        self.btn_toggle_roi.setCheckable(True) # Diventa un bottone on/off
        self.btn_toggle_roi.setEnabled(False)  # Disabilitato finché non c'è un'immagine
        self.main_layout.addWidget(self.btn_toggle_roi)

        self.btn_reset_roi = QPushButton("Resetta posizione linee")
        self.btn_reset_roi.setEnabled(False)
        self.main_layout.addWidget(self.btn_reset_roi)

        self.unwrapping_btn = QPushButton("Unwrap Faces")
        self.unwrapping_btn.setEnabled(False)
        self.main_layout.addWidget(self.unwrapping_btn)

        """
        COLLEGAMENTO ALLE ALTRE CLASSI
            Necessario farlo dopo la creazione delle viste e dei pulsanti ROI
        """
        self.roi_manager = ROIManager(self.view_sliceX, self.view_sliceY, self.view_sliceZ, 
                                      self.vm, self.main_layout, 
                                      self.btn_toggle_roi, self.btn_reset_roi, self.unwrapping_btn)
        
        
        """
        CONNESSIONI
        NB: quando si passano dei parametri alla funzione chiamata al momento del click è necessario usare "lambda:"
        """
        self.import_btn.clicked.connect(self._open_file_dialog)
        self.vm.volume_loaded.connect(self._setGridImage)

        self.btn_X_rot_left.clicked.connect(lambda: self._rotate_view(self.view_sliceX, -90))
        self.btn_X_rot_right.clicked.connect(lambda: self._rotate_view(self.view_sliceX, 90))
        self.btn_Y_rot_left.clicked.connect(lambda: self._rotate_view(self.view_sliceY, -90))
        self.btn_Y_rot_right.clicked.connect(lambda: self._rotate_view(self.view_sliceY, 90))
        self.btn_Z_rot_left.clicked.connect(lambda: self._rotate_view(self.view_sliceZ, -90))
        self.btn_Z_rot_right.clicked.connect(lambda: self._rotate_view(self.view_sliceZ, 90))

        self.btn_center_imageX.clicked.connect(lambda: self.view_sliceX.getView().autoRange())
        self.btn_center_imageY.clicked.connect(lambda: self.view_sliceY.getView().autoRange())
        self.btn_center_imageZ.clicked.connect(lambda: self.view_sliceZ.getView().autoRange())

        self.btn_toggle_roi.clicked.connect(self.roi_manager._toggle_roi_lines)
        self.btn_reset_roi.clicked.connect(lambda: self.roi_manager._toggle_roi_lines(True))
        
        self.unwrapping_btn.clicked.connect(lambda: self.vm._unwrap_current_volume(self.roi_manager.get_cut_coordinates()))
        self.vm.volume_unwrapped.connect(self._show_unwrapped_image)
        self.unwrappedImages = None

        self.vm.error_occurred.connect(self._show_popup_error_occurred)
        #------------------- Fine init ---------------------------

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 
                                                   "Select .tiff volume", 
                                                   "",
                                                   ".tiff images (*.tiff *.tif)")#il _ è perché la funzione _open_file_dialog di base restituisce una tupla di 2 elementi
        if file_path:
            self.vm._load_tiff(file_path)#funzione nel ViewModel

    def _setGridImage(self, tiff_volume_array : object): #questa funzione si occupera di proiettare le sezioni dell'immagine .tiff in tutte le sue prospettive-
        #Settaggio del 2D
        import numpy as np
        
        self.view_sliceX.setImage(np.transpose(tiff_volume_array, (2, 0, 1))) #letteralmente un setter
        self.view_sliceY.setImage(np.transpose(tiff_volume_array, (1, 0, 2)))
        self.view_sliceZ.setImage(tiff_volume_array)

        # Forza le immagini a partire da 0,0 nel sistema logico
        for view in [self.view_sliceX, self.view_sliceY, self.view_sliceZ]:
            view.getImageItem().setPos(0, 0)

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

        self.view_sliceX.getView().invertY(False)
        self.view_sliceY.getView().invertY(False)
        self.view_sliceZ.getView().invertY(False)

        self.btn_center_imageX.setEnabled(True)
        self.btn_center_imageY.setEnabled(True)
        self.btn_center_imageZ.setEnabled(True)

        self.btn_X_rot_left.setEnabled(True)
        self.btn_X_rot_right.setEnabled(True)
        self.btn_Y_rot_left.setEnabled(True)
        self.btn_Y_rot_right.setEnabled(True)
        self.btn_Z_rot_left.setEnabled(True)
        self.btn_Z_rot_right.setEnabled(True)

        self.btn_toggle_roi.setEnabled(True)

        #Impostazione di sicurezza di valori di default per le coordinate di unwrapping
        z_max, y_max, x_max = tiff_volume_array.shape
        self.unwrapping_values = {
            'Z': (0, z_max - 1),
            'Y': (0, y_max - 1),
            'X': (0, x_max - 1)
        }

    def _rotate_view(self, rotating_view, degrees):
        """
        Ruota l'inquadratura generale della scena (la vera 'telecamera').
        Questo evita che l'immagine esca dallo schermo e mantiene
        intatte le coordinate logiche per l'unwrapping e le linee.
        """
        view_box = rotating_view.getView()
        
        # Recupera il vero widget 'schermo' (QGraphicsView) che contiene la scena
        graphics_view = view_box.scene().views()[0]
        
        # Ruota la telecamera (in Qt, .rotate() somma automaticamente i gradi,
        # quindi non c'è più bisogno di tracciare la current_rotation)
        graphics_view.rotate(degrees)
        
        # Forza l'immagine a riadattarsi ai nuovi confini dello schermo
        view_box.autoRange()

    def _show_popup_error_occurred(self, msg: str):
        QMessageBox.critical(self, "Errore", msg)

    def _show_unwrapped_image(self, faces_list):
        self.unwrappedImages = UnwrappingViewWindow(faces_list)
        self.unwrappedImages.show()
