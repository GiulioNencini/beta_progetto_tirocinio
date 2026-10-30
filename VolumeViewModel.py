from PySide6.QtCore import QObject, Signal, Slot
import tifffile
class VolumeViewModel(QObject):
    volume_loaded = Signal(object)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        #FIXME allocare import e export manager se necessario

    def load_tiff(self, file_path: str):
        try:
            tiff_volume_array = tifffile.imread(file_path)
            self.volume_loaded.emit(tiff_volume_array)
        except Exception as e:
            self.error_occurred.emit(f"Errore durante l'importazione: {str(e)}")

        #importmanager
    