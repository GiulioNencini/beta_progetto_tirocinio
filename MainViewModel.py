from PySide6.QtCore import QObject, Signal, Slot
import tifffile
import myExceptions as mex
import numpy as np
import pyqtgraph.exporters
from PySide6.QtWidgets import QMessageBox

class MainViewModel(QObject):
    volume_loaded = Signal(object)

    error_occurred = Signal(str)

    volume_unwrapped = Signal(list)

    unwrapped_saved = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_volume = None

    def _loadTiffWithCheck(self, file_path: str):
        self.current_volume = tifffile.imread(file_path)
        if len(self.current_volume.shape) != 3:
            raise mex.InvalidTiffShape()

    @Slot()
    def _load_tiff(self, file_path: str):
        try:
            self._loadTiffWithCheck(file_path)
            print(f"Shape del TIFF: {self.current_volume.shape}")
            self.volume_loaded.emit(self.current_volume)
        except mex.InvalidTiffShape as e:
            self.error_occurred.emit(f"Il file tiff caricato ha una shape non valida: IMPOSSIBILE PROCESSARE")
        except Exception as e:
            self.error_occurred.emit(f"Errore durante l'importazione: {str(e)}")

    @Slot(dict)
    def _unwrap_current_volume(self, unwrapping_values : dict):
        if self.current_volume is None or unwrapping_values is None:
            self.error_occurred.emit("Impossibile eseguire l'unwrapping se non è caricato alcun file .tiff")
            return

        try:
            # Slicing delle 4 facce esterne come hai richiesto
            # NOTA: PyQtGraph gestisce in automatico la normalizzazione, quindi la matrice può subito essere gestita come segue
            uvs = unwrapping_values
            z_left, z_right = uvs['Z']
            y_bottom, y_top = uvs['Y']
            x_bottom, x_top = uvs['X']

            # NOTA: In NumPy e nei TIFF volumetrici, le matrici 3D seguono l'ordinamento delle dimensioni (Z, Y, X),
            # ovvero (Fette/Profondità, Righe, Colonne). Di conseguenza, il primo indice dell'array controlla l'asse Z 
            # (lo sviluppo longitudinale dello stack), il secondo l'asse Y (verticale) e il terzo l'asse X (orizzontale).

            
            # ribalta l'immagine rispetto alla sue
            face_1 = self.current_volume[z_left : z_right, y_top, x_bottom : x_top]
            face_2 = self.current_volume[z_left : z_right, y_bottom : y_top, x_top]
            face_3 = self.current_volume[z_left : z_right, y_bottom, x_bottom : x_top]
            face_4 = self.current_volume[z_left : z_right, y_bottom : y_top, x_bottom]

            # Emettiamo la lista delle 4 facce
            self.volume_unwrapped.emit([face_1, face_2, face_3, face_4])

        except Exception as e:
            self.error_occurred.emit(f"Errore durante l'unwrap: {str(e)}")

    def _export_unwrapped_image(self, file_path, right_view):
        try:
            # Utilizziamo l'esportatore interno di PyQtGraph
            # Così salverà la matrice con le esatte regolazioni colore/istogramma impostate visivamente dall'utente
            image_item = right_view.getImageItem()
            exporter = pyqtgraph.exporters.ImageExporter(image_item)
            
            # Risolve eventuali bug di pyqtgraph sulle dimensioni di esportazione forzando la lettura nativa
            exporter.export(file_path)
            self.unwrapped_saved.emit(f"Immagine salvata correttamente in:\n{file_path}")
        except Exception as e:
            self.error_occurred.emit(f"Si è verificato un errore durante l'esportazione:\n{str(e)}")