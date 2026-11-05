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
        self.line_Zview_topY = pqg.InfiniteLine(angle = 0, movable = True, pen = 'r')
        self.line_Zview_bottomY = pqg.InfiniteLine(angle = 0, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Zview_leftZ = pqg.InfiniteLine(angle = 90, movable = True, pen = 'b', hoverPen = 'b')
        self.line_Zview_rightZ = pqg.InfiniteLine(angle = 90, movable = True, pen = 'r')

        # Sulla vista Y (Coronale) definiamo il taglio in profondità Z
        self.line_Yview_topX = pqg.InfiniteLine(angle = 0, movable = True, pen = 'r')
        self.line_Yview_bottomX = pqg.InfiniteLine(angle = 0, movable = True, pen = 'b', hoverPen = 'b')

        self.all_lines = [
            self.line_Zview_topY, self.line_Zview_bottomY, self.line_Zview_leftZ, self.line_Zview_rightZ,
            self.line_Yview_topX, self.line_Yview_bottomX
        ]

        # Aggiungiamo le linee alle rispettive viste (nascoste all'inizio)
        #sono item interni ad esse
        self.view_sliceX.addItem(self.line_Zview_topY)
        self.view_sliceX.addItem(self.line_Zview_bottomY)
        self.view_sliceX.addItem(self.line_Zview_leftZ)
        self.view_sliceX.addItem(self.line_Zview_rightZ)
        
        self.view_sliceY.addItem(self.line_Yview_topX)
        self.view_sliceY.addItem(self.line_Yview_bottomX)
        
        #Aggiorna i bounds tra le linee, dopodiché attiva la funzione che (vedi sotto)
        #Aggiorna il valore delle coordinate quando si muovono con la connessione d'attesa
        for line in self.all_lines:
            line.hide()#evita che appaiano all'avvio del programma
            line.sigPositionChanged.connect(self._update_bounds_and_label)

    def _toggle_roi_lines(self, checked):
        """Mostra o nasconde le linee rosse."""
        self.btn_toggle_roi.setText("Disattiva Mirino (ROI)" if checked else "Attiva Mirino (ROI)")
        
        if checked:
            # Posizioniamo le LINEE AL CENTRO per renderle visibili al primo click
            center_x = self.view_sliceX.getImageItem().width() / 2
            center_y = self.view_sliceX.getImageItem().height() / 2
            center_z = self.view_sliceY.getImageItem().height() / 2
            
            self.line_Zview_leftZ.setValue(center_x - 50)
            self.line_Zview_rightZ.setValue(center_x + 50)
            self.line_Zview_topY.setValue(center_y + 50)
            self.line_Zview_bottomY.setValue(center_y - 50)
            
            self.line_Yview_topX.setValue(center_z + 50)
            self.line_Yview_bottomX.setValue(center_z - 50)
            
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
        y_bottom = int(self.line_Zview_bottomY.value())
        y_top = int(self.line_Zview_topY.value())
        z_left = int(self.line_Zview_leftZ.value())
        z_right = int(self.line_Zview_rightZ.value())

        self.lbl_coordinates.setText(
            f"Coordinate Taglio -> Z:[{z_left} a {z_right}] | Y:[{y_bottom} a {y_top}] | X:[{x_bottom} a {x_top}]"
        )

        self.unwrapping_values = {'Z': (z_left, z_right), 'Y': (y_bottom, y_top), 'X': (x_bottom, x_top)}

    def _update_bounds_and_label(self):
        # Impedisce a ZBottom (blu) di salire sopra ZTop (rossa) e viceversa
        self.line_Yview_bottomX.setBounds([0, self.line_Yview_topX.value()])
        self.line_Yview_topX.setBounds([self.line_Yview_bottomX.value(), self.vm.current_volume.shape[2]])
        
        # Limiti per l'asse Y nella vista Z
        self.line_Zview_bottomY.setBounds([0, self.line_Zview_topY.value()])
        self.line_Zview_topY.setBounds([self.line_Zview_bottomY.value(), self.vm.current_volume.shape[1]])
        
        # Limiti per l'asse X nella vista Z (Sinistra non può superare Destra)
        self.line_Zview_leftZ.setBounds([0, self.line_Zview_rightZ.value()])
        self.line_Zview_rightZ.setBounds([self.line_Zview_leftZ.value(), self.vm.current_volume.shape[0]])

        self._update_roi_label()

    def get_cut_coordinates(self):
        return self.unwrapping_values