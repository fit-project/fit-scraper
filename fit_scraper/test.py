import sys
import time
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QMovie

import os


class WorkerThread(QThread):
    finished = Signal()

    def run(self):
        time.sleep(5)  # Simula un'operazione lunga
        self.finished.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spinner con QMainWindow")

        self.button = QPushButton("Carica dati", self)
        self.button.clicked.connect(self.load_data)

        layout = QVBoxLayout()
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.spinner_overlay = QLabel(self)
        self.spinner_overlay.setAlignment(Qt.AlignCenter)
        self.spinner_overlay.setStyleSheet(
            "background-color: rgba(255, 255, 255, 180);"
        )
        self.spinner_overlay.setGeometry(0, 0, self.width(), self.height())
        self.spinner_overlay.hide()

        gif_path = os.path.abspath("spinner.gif")
        self.movie = QMovie(gif_path)

        print("GIF path:", gif_path)
        print("Exists?", os.path.exists(gif_path))

        self.spinner_overlay.setMovie(self.movie)
        self.showMaximized()

    def resizeEvent(self, event):
        self.spinner_overlay.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def load_data(self):
        self.button.setEnabled(False)
        self.spinner_overlay.show()
        self.movie.start()

        self.worker = WorkerThread()
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.start()

    def on_data_loaded(self):
        self.movie.stop()
        self.spinner_overlay.hide()
        self.button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
