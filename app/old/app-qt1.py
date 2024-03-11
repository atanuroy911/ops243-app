import sys
import queue
import json
import serial
import threading
import time
from datetime import datetime
import cv2
from collections import deque
import matplotlib.pyplot as plt
import seaborn as sns  # Import seaborn
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox, QLineEdit
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot

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

ser = serial.Serial(
    port='/dev/cu.usbmodem14201',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1,
    writeTimeout=2
)
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
        data = json.loads(strip_data)
        if 'speed' in data:
            return {'type': 'velocity', 'time': float(data['time']), 'speed': float(data['speed'])}
        elif 'range' in data:
            return {'type': 'range', 'time': float(data['time']), 'range': float(data['range'])}
    except:
        pass

class RealTimePlot(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-Time Plot")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.init_plots()
        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # Update plot every 100 milliseconds

    def init_plots(self):
        self.fig, (self.ax_velocity, self.ax_range) = plt.subplots(2, 1)

        self.line_velocity, = self.ax_velocity.plot([], [], 'b--', label='Velocity')
        self.ax_velocity.set_xlabel('Time')
        self.ax_velocity.set_ylabel('Velocity')
        self.ax_velocity.set_title('Real-Time Velocity Plot')

        self.line_range, = self.ax_range.plot([], [], 'r--', label='Range')
        self.ax_range.set_xlabel('Time')
        self.ax_range.set_ylabel('Range')
        self.ax_range.set_title('Real-Time Range Plot')

    def init_ui(self):
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

    def update_plot(self):
        data = ops_get_speed()
        if data:
            if data['type'] == 'velocity':
                self.line_velocity.set_xdata(list(self.line_velocity.get_xdata()) + [data['time']])
                self.line_velocity.set_ydata(list(self.line_velocity.get_ydata()) + [data['speed']])
                self.ax_velocity.relim()
                self.ax_velocity.autoscale_view()

            elif data['type'] == 'range':
                self.line_range.set_xdata(list(self.line_range.get_xdata()) + [data['time']])
                self.line_range.set_ydata(list(self.line_range.get_ydata()) + [data['range']])
                self.ax_range.relim()
                self.ax_range.autoscale_view()

            self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    window = RealTimePlot()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()