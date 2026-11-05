import pyqtgraph as pqg
from PySide6.QtWidgets import *
from PySide6.QtCore import *

class ROIManager:
    def __init__(self, view_sliceX, view_sliceY, view_sliceZ, view_model, main_layout : QVBoxLayout, btn_toggle_roi, btn_reset_roi, unwrapping_btn):
        self.view_sliceX = view_sliceX
        self.view_sliceY = view_sliceY
        self.view_sliceZ = view_sliceZ
        self.vm = view_model

        self.btn_toggle_roi = btn_toggle_roi
        self.btn_reset_roi = btn_reset_roi
        self.unwrapping_btn = unwrapping_btn

        self.z_max, self.y_max, self.x_max = self.vm.current_volume.shape
        self.unwrapping_values = {'Z': (0, self.z_max), 'Y': (0, self.y_max), 'X': (0, self.x_max)}

        self._is_syncing = False #questo flag serve eseguire le sincronizzazione delle linee verticali per Z senza rischiare loop di segnali indotti (ad esempio una linea ne muove un'altra che a sua volta rimuova la motrice)

        """
        SETTAGGIO LINEE BLU E ROSSE PER UNWRAPPING
        """
        #widget per farle apparire
        self.lbl_coordinates = QLabel("Coordinate ROI: ")
        self.lbl_coordinates.setStyleSheet("color: blue; font-weight: bold;")
        self.lbl_coordinates.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.lbl_coordinates)

        # Creazione delle linee rosse come InfiniteLine
        # Sulla vista Z (Assiale) definiamo il rettangolo X-Y (Top, Bottom, Left, Right)
        self.line_Xview_topY = pqg.InfiniteLine(angle = 0, movable = True, pen = 'r')
        self.line_Xview_bottomY = pqg.InfiniteLine(angle = 0, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Xview_leftZ = pqg.InfiniteLine(angle = 90, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Xview_rightZ = pqg.InfiniteLine(angle = 90, movable = True, pen = 'r')

        # Sulla vista Y (Coronale) definiamo il taglio in profondità Z
        self.line_Yview_topX = pqg.InfiniteLine(angle = 0, movable = True, pen = 'r')
        self.line_Yview_bottomX = pqg.InfiniteLine(angle = 0, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Yview_leftZ = pqg.InfiniteLine(angle = 90, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Yview_rightZ = pqg.InfiniteLine(angle = 90, movable = True, pen = 'r')

        self.all_lines = (
            self.line_Xview_topY, self.line_Xview_bottomY, self.line_Xview_leftZ, self.line_Xview_rightZ,
            self.line_Yview_topX, self.line_Yview_bottomX, self.line_Yview_leftZ, self.line_Yview_rightZ
        )

        # Aggiungiamo le linee alle rispettive viste (nascoste all'inizio)
        #sono item interni ad esse
        self.view_sliceX.addItem(self.line_Xview_topY)
        self.view_sliceX.addItem(self.line_Xview_bottomY)
        self.view_sliceX.addItem(self.line_Xview_leftZ)
        self.view_sliceX.addItem(self.line_Xview_rightZ)
        
        self.view_sliceY.addItem(self.line_Yview_topX)
        self.view_sliceY.addItem(self.line_Yview_bottomX)
        self.view_sliceY.addItem(self.line_Yview_leftZ)
        self.view_sliceY.addItem(self.line_Yview_rightZ)
        
        #Aggiorna i bounds tra le linee, dopodiché attiva la funzione che (vedi sotto)
        #Aggiorna il valore delle coordinate quando si muovono con la connessione d'attesa
        for line in self.all_lines:
            line.hide()#evita che appaiano all'avvio del programma
            line.sigPositionChanged.connect(self._update_bounds_and_label)

        #Sincroniziamo le linee verticali Z in entrambe le viste
        self.line_Xview_leftZ.sigPositionChanged.connect(self._sync_Z_left)
        self.line_Yview_leftZ.sigPositionChanged.connect(self._sync_Z_left)
        self.line_Xview_rightZ.sigPositionChanged.connect(self._sync_Z_right)
        self.line_Yview_rightZ.sigPositionChanged.connect(self._sync_Z_right)

    def _sync_Z_left(self, source_line):
        if self._is_syncing: 
            return
        self._is_syncing = True
        target = self.line_Yview_leftZ if source_line == self.line_Xview_leftZ else self.line_Xview_leftZ
        target.setValue(source_line.value())
        self._is_syncing = False

    def _sync_Z_right(self, source_line):
        if self._is_syncing: 
            return
        self._is_syncing = True
        target = self.line_Yview_rightZ if source_line == self.line_Xview_rightZ else self.line_Xview_rightZ
        target.setValue(source_line.value())
        self._is_syncing = False

    def _toggle_roi_lines(self, checked):
        """Mostra o nasconde le linee rosse."""
        self.btn_toggle_roi.setText("Disattiva Mirino (ROI)" if checked else "Attiva Mirino (ROI)")
        
        if checked:
            self.__setLinesValues__()
            
            for line in self.all_lines:
                line.show()
            
            self._update_roi_label()#serve anche per settere i valori di deafult per l'unwrapping
            self.btn_reset_roi.setEnabled(True)
            self.unwrapping_btn.setEnabled(True)
        else:
            for line in self.all_lines:
                line.hide()
            
            self.lbl_coordinates.setText("Coordinate di taglio disattivate")
            self.btn_reset_roi.setEnabled(False)
            self.unwrapping_btn.setEnabled(False)

    def _update_roi_label(self):
        """Legge la posizione delle linee e aggiorna la label testuale.
        I valori castati a intero rappresentano i pixel di taglio"""
        x_top = int(self.line_Yview_topX.value())
        x_bottom = int(self.line_Yview_bottomX.value())
        y_bottom = int(self.line_Xview_bottomY.value())
        y_top = int(self.line_Xview_topY.value())
        z_left = int(self.line_Xview_leftZ.value())
        z_right = int(self.line_Xview_rightZ.value())

        self.lbl_coordinates.setText(
            f"Coordinate Taglio -> Z:[{z_left} a {z_right}] | Y:[{y_bottom} a {y_top}] | X:[{x_bottom} a {x_top}]"
        )

        self.unwrapping_values = {'Z': (z_left, z_right), 'Y': (y_bottom, y_top), 'X': (x_bottom, x_top)}

    def _update_bounds_and_label(self):
        # Impedisce a XBottom (blu) di salire sopra XTop (rossa) e viceversa
        self.line_Yview_bottomX.setBounds([0, self.line_Yview_topX.value()])
        self.line_Yview_topX.setBounds([self.line_Yview_bottomX.value(), self.vm.current_volume.shape[2]])
        
        # Limiti per l'asse Y nella vista Z
        self.line_Xview_bottomY.setBounds([0, self.line_Xview_topY.value()])
        self.line_Xview_topY.setBounds([self.line_Xview_bottomY.value(), self.vm.current_volume.shape[1]])
        
        # Limiti per l'asse Z nella vista X e Y (Sinistra non può superare Destra)
        self.line_Xview_leftZ.setBounds([0, self.line_Xview_rightZ.value()])
        self.line_Xview_rightZ.setBounds([self.line_Xview_leftZ.value(), self.vm.current_volume.shape[0]])
        self.line_Yview_leftZ.setBounds([0, self.line_Yview_rightZ.value()])
        self.line_Yview_rightZ.setBounds([self.line_Yview_leftZ.value(), self.vm.current_volume.shape[0]])
        
        self._update_roi_label()

    def _reset_roi_lines(self):
        self.unwrapping_values = {'Z': (0, self.z_max), 'Y': (0, self.y_max), 'X': (0, self.x_max)}
        self.__setLinesValues__()
        self._update_roi_label()

    def get_cut_coordinates(self):
        return self.unwrapping_values

    def __setLinesValues__(self):
        #disconnessione segnali per evitare loop di segnali durante il setting manuale
        for line in self.all_lines:
            try: line.sigPositionChanged.disconnect(self._update_bounds_and_label)
            except RuntimeError: pass

        try:
            self.line_Xview_leftZ.sigPositionChanged.disconnect(self._sync_Z_left)
            self.line_Yview_leftZ.sigPositionChanged.disconnect(self._sync_Z_left)
            self.line_Xview_rightZ.sigPositionChanged.disconnect(self._sync_Z_right)
            self.line_Yview_rightZ.sigPositionChanged.disconnect(self._sync_Z_right)
        except RuntimeError: pass

        uwv = self.unwrapping_values
        leftZ, rightZ = uwv.get('Z')
        bottomY, topY = uwv.get('Y')
        bottomX, topX = uwv.get('X')
        self.line_Xview_leftZ.setValue(leftZ)
        self.line_Xview_rightZ.setValue(rightZ)
        self.line_Xview_bottomY.setValue(bottomY)
        self.line_Xview_topY.setValue(topY)
        
        self.line_Yview_leftZ.setValue(leftZ)
        self.line_Yview_rightZ.setValue(rightZ)
        self.line_Yview_bottomX.setValue(bottomX)
        self.line_Yview_topX.setValue(topX)

        # Riconnetti i segnali
        for line in self.all_lines:
            line.sigPositionChanged.connect(self._update_bounds_and_label)
            
        self.line_Xview_leftZ.sigPositionChanged.connect(self._sync_Z_left)
        self.line_Yview_leftZ.sigPositionChanged.connect(self._sync_Z_left)
        self.line_Xview_rightZ.sigPositionChanged.connect(self._sync_Z_right)
        self.line_Yview_rightZ.sigPositionChanged.connect(self._sync_Z_right)