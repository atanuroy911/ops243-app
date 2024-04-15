import sys
import queue
import json
import serial
import threading
import time
import datetime
import csv
from datetime import datetime
import cv2
from collections import deque
import matplotlib.pyplot as plt
from PyQt5.QtGui import QPixmap, QImage
import seaborn as sns  # Import seaborn
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QLineEdit, QMessageBox
from PyQt5.QtCore import QTimer, QObject, QThread, pyqtSignal, pyqtSlot, Qt

# Initialize seaborn
sns.set()

def send_serial_cmd(print_prefix, command):
    """
    function for sending serial commands to the OPS module
    """
    data_for_send_str = command
    data_for_send_bytes = str.encode(data_for_send_str)
    print(print_prefix, command)
    ser.write(data_for_send_bytes)
    # initialize message verify checking
    ser_message_start = '{'
    ser_write_verify = False
    # print out module response to command string
    while not ser_write_verify:
        data_rx_bytes = ser.readline()
        data_rx_length = len(data_rx_bytes)
        if data_rx_length != 0:
            data_rx_str = str(data_rx_bytes)
            if data_rx_str.find(ser_message_start):
                ser_write_verify = True

def send_data_to_arduino(data):
    """
    Function to send data to Arduino over serial connection
    """
    # Convert data to string
    data_str = ','.join(map(str, data)) + '\n'
    # Encode string to bytes
    data_bytes = data_str.encode('utf-8')
    # Write data to Arduino serial connection
    arduino_serial.write(data_bytes)

ser = serial.Serial(
    port='COM7',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1,
    writeTimeout=2
)

# Open serial connection to Arduino
arduino_serial = serial.Serial('COM10', 9600)  # Replace 'COM10' with appropriate port for Arduino

ser.flushInput()
ser.flushOutput()

last_velocity = 0
last_range = 0

# constants for the OPS module
Ops_Speed_Output_Units = ["US", "UK", "UM", "UC"]
Ops_Speed_Output_Units_lbl = ["mph", "km/h", "m/s", "cm/s"]
Ops_Blanks_Pref_Zero = "BZ"
Ops_Sampling_Frequency = "SX"
Ops_Transmit_Power = "PX"
Ops_Threshold_Control = "MX"
Ops_Module_Information = "??"
Ops_Overlook_Buffer = "OZ"
Ops_Json_Output = "OJ"
Ops_Mag_Output = "OM"
Ops_Detect_Object_Output = "ON"
Ops_Time_Set = "OT"
Ops_TimeHuman_Set = "OH"
Ops_Set_Sampling_Rate = "SI"
# Ops_Delayed_Report = "W1"

# initialize the OPS module
send_serial_cmd("\nOverlook buffer", Ops_Overlook_Buffer)
send_serial_cmd("\nSet Speed Output Units: ", Ops_Speed_Output_Units[1])
send_serial_cmd("\nSet Sampling Frequency: ", Ops_Sampling_Frequency)
send_serial_cmd("\nSet Transmit Power: ", Ops_Transmit_Power)
send_serial_cmd("\nSet Threshold Control: ", Ops_Threshold_Control)
send_serial_cmd("\nSet Blanks Preference: ", Ops_Blanks_Pref_Zero)
send_serial_cmd("\nSet Json Preference: ", Ops_Json_Output)
send_serial_cmd("\nSet Mag Preference: ", Ops_Mag_Output)
send_serial_cmd("\nSet Sampling Preference: ", Ops_Set_Sampling_Rate)
send_serial_cmd("\nSet Time Preference: ", Ops_Time_Set)
# send_serial_cmd("\nSet Time Delay: ", Ops_Delayed_Report)

print("SERVICE STARTED")

def ops_get_speed():
    """
    capture speed reading from OPS module
    """
    try:
        Ops_rx_bytes = ser.readline()
        strip_data = Ops_rx_bytes.decode("utf-8").strip()
        arduino_data = strip_data.split(',')
        send_data_to_arduino(arduino_data)
        data = json.loads(strip_data)
        if 'speed' in data:
            return {'type': 'velocity', 'time': float(data['time']), 'speed': float(data['speed'])}
        elif 'range' in data:
            return {'type': 'range', 'time': float(data['time']), 'range': float(data['range'])}
    except:
        pass
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
        
class RealTimePlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Plot")
        self.setGeometry(100, 100, 1024, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Left side layout
        self.left_layout = QVBoxLayout()
        self.layout.addLayout(self.left_layout)
        
        label_style = """
                QLabel {
                    font-weight: bold;
                    font-size: 20px;
                    color: #333; /* Text color */
                    background-color: #f0f0f0; /* Background color */
                    border: 2px solid #ccc; /* Border */
                    padding: 5px; /* Padding */
                    border-radius: 5px; /* Border radius */
                    min-width: 100px; /* Set minimum width */
                    min-height: 40px; /* Set minimum height */
                }
            """
        # Labels for displaying current speed and range
        self.range_label = QLabel(self)
        self.range_label.setStyleSheet(label_style)
        self.speed_label = QLabel(self)
        self.speed_label.setStyleSheet(label_style)
        self.left_layout.addWidget(self.range_label)
        self.left_layout.addWidget(self.speed_label)

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
        
        self.init_plots()
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # Update plot every 100 milliseconds
        
        self.recording = False
        self.recorded_data = []

        self.record_start_button.clicked.connect(self.start_recording)
        self.record_stop_button.clicked.connect(self.stop_recording)

        self.camera_thread = CameraThread()
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread_thread = None
        self.start_camera()
        
        # self.send_button.clicked.connect(self.send_data)

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
        
    def init_plots(self):
        # Spinner for selecting the number of data points to display
        self.data_points_spinner = QSpinBox(self)
        self.data_points_spinner.setRange(1, 1000)  # Set the range as per your requirement
        self.data_points_spinner.setValue(100)  # Set default value to 100
        self.right_layout.addWidget(self.data_points_spinner)
        
        self.fig, (self.ax_velocity, self.ax_range) = plt.subplots(2, 1)

        self.line_velocity, = self.ax_velocity.plot([], [], 'b-', label='Velocity')
        self.ax_velocity.set_xlabel('Time')
        self.ax_velocity.set_ylabel('Velocity')
        self.ax_velocity.set_title('Real-Time Velocity Plot')

        self.line_range, = self.ax_range.plot([], [], 'r-', label='Range')
        self.ax_range.set_xlabel('Time')
        self.ax_range.set_ylabel('Range')
        self.ax_range.set_title('Real-Time Range Plot')

    def init_ui(self):
        self.canvas = FigureCanvas(self.fig)
        self.right_layout.addWidget(self.canvas)

    def update_plot(self):
        data = ops_get_speed()
        if data:
            if self.recording:
                self.recorded_data.append(data)
                # Update field names with any new keys from the received data
                self.recorded_fieldnames.update(data.keys())
            if data['type'] == 'velocity':
                self.line_velocity.set_xdata(list(self.line_velocity.get_xdata())[-self.data_points_spinner.value():] + [data['time']])
                self.line_velocity.set_ydata(list(self.line_velocity.get_ydata())[-self.data_points_spinner.value():] + [data['speed']])
                
                self.speed_label.setText(f"Current Speed: {data['speed']}")
                
                # Add marker at each data point 
                # self.ax_velocity.plot(data['time'], data['speed'], 'bo')
                
                self.ax_velocity.relim()
                self.ax_velocity.autoscale_view()

            elif data['type'] == 'range':
                self.line_range.set_xdata(list(self.line_range.get_xdata())[-self.data_points_spinner.value():] + [data['time']])
                self.line_range.set_ydata(list(self.line_range.get_ydata())[-self.data_points_spinner.value():] + [data['range']])
                
                self.range_label.setText(f"Current Range: {data['range']}")

                # Add marker at each data point
                # self.ax_range.plot(data['time'], data['range'], 'ro')
                
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
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"recorded_data_{current_time}.csv"
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=list(self.recorded_fieldnames))
                writer.writeheader()
                print(self.recorded_fieldnames)
                for data in self.recorded_data:
                    writer.writerow({key: data.get(key, '') for key in self.recorded_fieldnames})

    def closeEvent(self, event):
        if self.recording:
            reply = QMessageBox.question(self, 'Message', "Do you want to save recorded data before closing?",
                                        QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Close,
                                        QMessageBox.Save)

            if reply == QMessageBox.Save:
                self.save_to_csv()
                event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        
        else:
            reply = QMessageBox.question(self, 'Message', "Do you want to close?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
            else:
                event.accept()
def main():
    app = QApplication(sys.argv)
    window = RealTimePlot()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
