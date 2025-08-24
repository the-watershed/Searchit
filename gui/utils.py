from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool


class WorkerSignals(QObject):
	result = pyqtSignal(object)
	error = pyqtSignal(Exception)
	finished = pyqtSignal()


class Worker(QRunnable):
	"""Generic QRunnable to execute a function in a background thread.
	Do not interact with Qt widgets from the worker; use signals.
	"""
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
			try:
				self.signals.error.emit(e)
			except Exception:
				pass
		finally:
			try:
				self.signals.finished.emit()
			except Exception:
				pass


def run_in_thread(fn, *args, on_result=None, on_error=None, on_finished=None, **kwargs):
	"""Run fn(*args, **kwargs) in a background thread. Optionally connect callbacks.
	Returns the Worker instance; it is started immediately on the global thread pool.
	"""
	worker = Worker(fn, *args, **kwargs)
	if on_result:
		worker.signals.result.connect(on_result)
	if on_error:
		worker.signals.error.connect(on_error)
	if on_finished:
		worker.signals.finished.connect(on_finished)
	QThreadPool.globalInstance().start(worker)
	return worker
