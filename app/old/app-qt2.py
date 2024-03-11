import sys
import queue
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import cv2
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QLineEdit
from PyQt5.QtCore import QTimer, QObject, QThread, pyqtSignal, pyqtSlot, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from serial_ops import start_ops_thread

class CameraThread(QObject):
    frame_ready = pyqtSignal(object)

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def run(self):
        camera = cv2.VideoCapture(0)  # 0 for default camera, change if needed
        while True:
            ret, frame = camera.read()
            if ret:
                self.frame_ready.emit(frame)
        camera.release()

class DataThread(QObject):
    data_ready = pyqtSignal(dict)

    def __init__(self, port):
        super().__init__()
        self.data_queue = start_ops_thread(port)

    @pyqtSlot()
    def run(self):
        while True:
            try:
                data = self.data_queue.get(timeout=1)
                self.data_ready.emit(data)
            except queue.Empty:
                pass

class RealTimePlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Plot")
        self.setGeometry(100, 100, 1000, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Left side layout
        self.left_layout = QVBoxLayout()
        self.layout.addLayout(self.left_layout)

        # Camera feed
        self.camera_label = QLabel(self)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.camera_label)

        # Box and send button
        self.data_entry_box = QLineEdit(self)
        self.left_layout.addWidget(self.data_entry_box)
        self.send_button = QPushButton("Send")
        self.left_layout.addWidget(self.send_button)

        # Start and stop recording
        self.record_start_button = QPushButton("Start Recording")
        self.left_layout.addWidget(self.record_start_button)
        self.record_stop_button = QPushButton("Stop Recording")
        self.left_layout.addWidget(self.record_stop_button)
        self.record_stop_button.setEnabled(False)

        # Right side layout for plots
        self.right_layout = QVBoxLayout()
        self.layout.addLayout(self.right_layout)

        self.fig, (self.ax_speed, self.ax_range) = plt.subplots(2, 1)
        self.canvas = FigureCanvas(self.fig)
        self.right_layout.addWidget(self.canvas)

        self.line_speed, = self.ax_speed.plot([], [], 'b-', label='Speed')  # Smooth line
        self.line_range, = self.ax_range.plot([], [], 'r-', label='Range')  # Smooth line
        self.ax_speed.set_xlabel('Time')
        self.ax_speed.set_ylabel('Speed')
        self.ax_speed.set_title('Real-Time Speed Plot')
        self.ax_range.set_xlabel('Time')
        self.ax_range.set_ylabel('Range')
        self.ax_range.set_title('Real-Time Range Plot')
        self.ax_speed.legend(loc='upper left')
        self.ax_range.legend(loc='upper left')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)

        self.data_thread = DataThread("/dev/cu.usbmodem14201")
        self.data_thread.data_ready.connect(self.handle_data)
        self.data_thread_thread = None

        sns.set()

        self.num_data_points = 100
        self.recording = False
        self.recorded_data = []

        self.record_start_button.clicked.connect(self.start_recording)
        self.record_stop_button.clicked.connect(self.stop_recording)

        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread_thread = None
        self.start_camera()

        self.send_button.clicked.connect(self.send_data)

    def start_camera(self):
        if self.camera_thread_thread is None or not self.camera_thread_thread.isRunning():
            self.camera_thread_thread = QThread()
            self.camera_thread.moveToThread(self.camera_thread_thread)
            self.camera_thread_thread.started.connect(self.camera_thread.run)
            self.camera_thread_thread.start()

    @pyqtSlot(object)
    def update_camera(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        convert_to_qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_qt_format.scaled(self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio)
        self.camera_label.setPixmap(QPixmap.fromImage(p))

    def start_data_thread(self):
        if self.data_thread_thread is None or not self.data_thread_thread.isRunning():
            self.data_thread_thread = QThread()
            self.data_thread.moveToThread(self.data_thread_thread)
            self.data_thread_thread.started.connect(self.data_thread.run)
            self.data_thread_thread.start()

    @pyqtSlot(dict)
    def handle_data(self, data):
        if 'speed' in data or 'range' in data:
            print(type(data))
            if self.recording:
                self.recorded_data.append(data)
                # Update field names with any new keys from the received data
                self.recorded_fieldnames.update(data.keys())
            self.update_plot(data)

    def update_plot(self, data=None):
        if data is not None:
            if 'speed' in data:
                x_speed = float(data['time'])
                y_speed = float(data['speed'])
                self.line_speed.set_xdata(list(self.line_speed.get_xdata())[-self.num_data_points:] + [x_speed])
                self.line_speed.set_ydata(list(self.line_speed.get_ydata())[-self.num_data_points:] + [y_speed])
                self.ax_speed.relim()
                self.ax_speed.autoscale_view()

            if 'range' in data:
                x_range = float(data['time'])
                y_range = float(data['range'])
                self.line_range.set_xdata(list(self.line_range.get_xdata())[-self.num_data_points:] + [x_range])
                self.line_range.set_ydata(list(self.line_range.get_ydata())[-self.num_data_points:] + [y_range])
                self.ax_range.relim()
                self.ax_range.autoscale_view()

            self.canvas.draw()

    def start_recording(self):
        self.recording = True
        self.recorded_data = []
        self.recorded_fieldnames = set()  # Initialize an empty set for field names
        self.record_start_button.setEnabled(False)
        self.record_stop_button.setEnabled(True)

    @pyqtSlot()
    def stop_recording(self):
        self.recording = False
        self.record_start_button.setEnabled(True)
        self.record_stop_button.setEnabled(False)
        self.save_to_csv()

    def save_to_csv(self):
        if self.recorded_data:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"recorded_data_{current_time}.csv"
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=list(self.recorded_fieldnames))
                writer.writeheader()
                for data in self.recorded_data:
                    writer.writerow({key: data.get(key, '') for key in self.recorded_fieldnames})

    def send_data(self):
        data = self.data_entry_box.text()
        # Here you can handle sending the data
        print("Sending data:", data)

def main():
    app = QApplication(sys.argv)
    window = RealTimePlot()
    window.show()
    window.start_data_thread()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()