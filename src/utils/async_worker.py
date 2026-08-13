from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(object)
    result = pyqtSignal(object)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            res = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(res)
        except Exception as e:
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()

def run_async(fn, *args, on_result=None, on_error=None, on_finished=None, **kwargs):
    worker = Worker(fn, *args, **kwargs)
    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    if on_finished:
        worker.signals.finished.connect(on_finished)
    QThreadPool.globalInstance().start(worker)
