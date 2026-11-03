from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor
import pyqtgraph as pqg
from VolumeViewModel import *
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

    view = pqg.ImageView()
    view.ui.roiBtn.hide()
    view.ui.menuBtn.hide()
    layout.addWidget(view)

    grid.addWidget(container, row_in_grid, col_in_grid)

    return view, center_image_btn, left_rot_btn, right_rot_btn

class VolumeView(QWidget):
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

        self.view_sliceX, self.btn_center_imageX, self.btn_X_rot_left, self.btn_X_rot_right = create_titled_view("Vista Asse X (Sagittale)", self.grid, 0, 1)
        self.view_sliceY, self.btn_center_imageY, self.btn_Y_rot_left, self.btn_Y_rot_right = create_titled_view("Vista Asse Y (Coronale)", self.grid, 1, 0)
        self.view_sliceZ, self.btn_center_imageZ, self.btn_Z_rot_left, self.btn_Z_rot_right = create_titled_view("Vista Asse Z (Assiale)", self.grid, 1, 1)

        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 1)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)

        #FOR per nascondere i menù superflui
        for view in [self.view_sliceX, self.view_sliceY, self.view_sliceZ]:
            view.ui.roiBtn.hide()
            view.ui.menuBtn.hide()


        """
        SETTAGGIO LINEE ROSSE PER UNWRAPPING
        """
        #widget per farle apparire
        self.lbl_coordinates = QLabel("Coordinate ROI: ")
        self.lbl_coordinates.setStyleSheet("color: blue; font-weight: bold;")
        self.lbl_coordinates.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.lbl_coordinates)

        #inizializiamo il pulsante per attivare/disattivare le linee
        #quindi attivare o disattivare la selezione delle coordinate per l'unwrapping
        self.btn_toggle_roi = QPushButton("Attiva Mirino (ROI)")
        self.btn_toggle_roi.setCheckable(True) # Diventa un bottone on/off
        self.btn_toggle_roi.setEnabled(False)  # Disabilitato finché non c'è un'immagine
        self.main_layout.addWidget(self.btn_toggle_roi)

        # Creazione delle linee rosse come InfiniteLine
        # Sulla vista Z (Assiale) definiamo il rettangolo X-Y (Top, Bottom, Left, Right)
        self.line_Zview_topY = pqg.InfiniteLine(angle = 0, movable = True, pen = 'r')
        self.line_Zview_bottomY = pqg.InfiniteLine(angle = 0, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Zview_leftX = pqg.InfiniteLine(angle = 90, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Zview_rightX = pqg.InfiniteLine(angle = 90, movable = True, pen = 'r')

        # Sulla vista Y (Coronale) definiamo il taglio in profondità Z
        self.line_Yview_topZ = pqg.InfiniteLine(angle = 0, movable = True, pen = 'r')
        self.line_Yview_bottomZ = pqg.InfiniteLine(angle = 0, movable = True, pen = 'b', hoverPen = 'b')

        self.all_lines = [
            self.line_Zview_topY, self.line_Zview_bottomY, self.line_Zview_leftX, self.line_Zview_rightX,
            self.line_Yview_topZ, self.line_Yview_bottomZ
        ]

        # Aggiungiamo le linee alle rispettive viste (nascoste all'inizio)
        #sono item interni ad esse
        self.view_sliceZ.addItem(self.line_Zview_topY)
        self.view_sliceZ.addItem(self.line_Zview_bottomY)
        self.view_sliceZ.addItem(self.line_Zview_leftX)
        self.view_sliceZ.addItem(self.line_Zview_rightX)
        
        self.view_sliceY.addItem(self.line_Yview_topZ)
        self.view_sliceY.addItem(self.line_Yview_bottomZ)
        
        #Aggiorna i bounds tra le linee, dopodiché attiva la funzione che (vedi sotto)
        #Aggiorna il valore delle coordinate quando si muovono con la connessione d'attesa
        for line in self.all_lines:
            line.hide()#evita che appaiano all'avvio del programma
            line.sigPositionChanged.connect(self._update_bounds_and_label)
        
        # Connessione per mostrare/nascondere le linee
        self.btn_toggle_roi.toggled.connect(self._toggle_roi_lines)

        self.btn_reset_roi = QPushButton("Resetta posizione linee")
        self.btn_reset_roi.setEnabled(False)
        self.main_layout.addWidget(self.btn_reset_roi)


        """
        UNWRAPPING
        """
        self.unwrapping_btn = QPushButton("Unwrap Faces")
        self.unwrapping_btn.setEnabled(False)
        self.main_layout.addWidget(self.unwrapping_btn)

        self.unwrapContainer = QWidget()#il contenitore delle 4
        self.unwrapContainer.setMinimumHeight(300)
        self.unwrap_layout = QHBoxLayout(self.unwrapContainer)
        self.unwrap_layout.setContentsMargins(0, 0, 0, 0)
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

        self.btn_toggle_roi.clicked.connect(self._toggle_roi_lines)
        self.btn_reset_roi.clicked.connect(lambda: self._toggle_roi_lines(True))

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
        self.unwrapping_btn.setEnabled(True)

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

    def _toggle_roi_lines(self, checked):
        """Mostra o nasconde le linee rosse."""
        self.btn_toggle_roi.setText("Disattiva Mirino (ROI)" if checked else "Attiva Mirino (ROI)")
        
        if checked:
            # Posizioniamo le LINEE AL CENTRO per renderle visibili al primo click
            center_x = self.view_sliceZ.getImageItem().width() / 2
            center_y = self.view_sliceZ.getImageItem().height() / 2
            center_z = self.view_sliceY.getImageItem().height() / 2
            
            self.line_Zview_leftX.setValue(center_x - 50)
            self.line_Zview_rightX.setValue(center_x + 50)
            self.line_Zview_topY.setValue(center_y + 50)
            self.line_Zview_bottomY.setValue(center_y - 50)
            
            self.line_Yview_topZ.setValue(center_z + 50)
            self.line_Yview_bottomZ.setValue(center_z - 50)
            
            for line in self.all_lines:
                line.show()
            self._update_roi_label()
            self.btn_reset_roi.setEnabled(True)
        else:
            for line in self.all_lines:
                line.hide()
            self.lbl_coordinates.setText("Coordinate di taglio disattivate")
            self.btn_reset_roi.setEnabled(False)

    def _update_roi_label(self):
        """Legge la posizione delle linee e aggiorna la label testuale."""
        # I valori castati a intero rappresentano i pixel di taglio
        z_top = int(self.line_Yview_topZ.value())
        z_bottom = int(self.line_Yview_bottomZ.value())
        y_bottom = int(self.line_Zview_bottomY.value())
        y_top = int(self.line_Zview_topY.value())
        x_left = int(self.line_Zview_leftX.value())
        x_right = int(self.line_Zview_rightX.value())

        self.lbl_coordinates.setText(
            f"Coordinate Taglio -> X:[{x_left} a {x_right}] | Y:[{y_bottom} a {y_top}] | Z:[{z_bottom} a {z_top}]"
        )

    def _update_bounds_and_label(self):
        # Impedisce a ZBottom (blu) di salire sopra ZTop (rossa) e viceversa
        self.line_Yview_bottomZ.setBounds([None, self.line_Yview_topZ.value()])
        self.line_Yview_topZ.setBounds([self.line_Yview_bottomZ.value(), None])
        
        # Limiti per l'asse Y nella vista Z
        self.line_Zview_bottomY.setBounds([None, self.line_Zview_topY.value()])
        self.line_Zview_topY.setBounds([self.line_Zview_bottomY.value(), None])
        
        # Limiti per l'asse X nella vista Z (Sinistra non può superare Destra)
        self.line_Zview_leftX.setBounds([None, self.line_Zview_rightX.value()])
        self.line_Zview_rightX.setBounds([self.line_Zview_leftX.value(), None])

        self._update_roi_label()

    def _show_unwrapped_image(self, faces_list: list):
        self.unwrapContainer.show()
        for i, face_array in enumerate(faces_list):
            #autoRange serve per orientare correttamente le proiezioni lungo l'asse Z
            self.unwrapped_views[i].setImage(face_array, autoRange = True)#sono quattro spazi vuoti che vengono riempiti proprio come accade al momento del caricamento del file