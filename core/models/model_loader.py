from PyQt5.QtCore import QObject, pyqtSignal

class ModelLoader(QObject):
    finished = pyqtSignal(list)
    
    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def run(self):
        try:
            result = self.handler.list_local_models()
            models = [m['name'] for m in result.get('models', [])]
            self.finished.emit(models)
        except Exception as e:
            self.finished.emit([])
            