from PySide6.QtCore import QObject, Signal, Slot
import tifffile
class VolumeViewModel(QObject):
    volume_loaded = Signal(object)

    error_occurred = Signal(str)

    volume_unwrapped = Signal(list)

    def __init__(self):
        super().__init__()
        self.current_volume = None
        #FIXME allocare import e export manager se necessario

    @Slot()
    def load_tiff(self, file_path: str):
        try:
            self.current_volume = tifffile.imread(file_path)
            self.volume_loaded.emit(self.current_volume)
        except Exception as e:
            self.error_occurred.emit(f"Errore durante l'importazione: {str(e)}")

    @Slot()
    def unwrap_current_volume(self):
        if self.current_volume is None:
            self.error_occurred.emit("Impossibile eseguire l'unwrapping se non è caricato alcun file .tiff")
            return

        try:
            # Slicing delle 4 facce esterne come hai richiesto
            # NOTA: PyQtGraph gestisce in automatico la normalizzazione, quindi la matrice può subito essere gestita come segue
            face_1 = self.current_volume[:, 0, :]
            face_2 = self.current_volume[:, :, 0]
            face_3 = self.current_volume[:, -1, :]
            face_4 = self.current_volume[:, :, -1]
            
            # Emettiamo la lista delle 4 facce
            self.volume_unwrapped.emit([face_1, face_2, face_3, face_4])
        except Exception as e:
            self.error_occurred.emit(f"Errore durante l'unwrap: {str(e)}")
