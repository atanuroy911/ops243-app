import wx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from collections import deque
import json
import serial
import csv
import time
from datetime import datetime
import threading  # Import threading module

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
Ops_Set_Sampling_Rate = "SX"

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

class RealTimePlot(wx.Frame):
    def __init__(self, parent, title):
        super(RealTimePlot, self).__init__(parent, title=title, size=(800, 600))

        self.recording = False
        self.interval_time = 1  # Default interval time for matplotlib animation

        self.init_ui()

    def init_ui(self):
        self.panel = wx.Panel(self)

        # Create a common figure that contains both velocity and range plots
        self.fig, (self.ax_velocity, self.ax_range) = plt.subplots(2, 1)

        # Create a line for velocity plot
        self.line_velocity, = self.ax_velocity.plot([], [], lw=2, marker='o')
        self.ax_velocity.grid()
        self.ax_velocity.set_title('Velocity')
        self.ax_velocity.set_ylim(0, 5)  # Set y-axis limits as per your data range

        # Create a line for range plot
        self.line_range, = self.ax_range.plot([], [], lw=2, marker='o')
        self.ax_range.grid()
        self.ax_range.set_title('Range')
        self.ax_range.set_ylim(0, 10)  # Set y-axis limits as per your data range

        # Create deques to store data points for plotting
        self.xdata_velocity = deque(maxlen=100)
        self.ydata_velocity = deque(maxlen=100)
        self.xdata_range = deque(maxlen=100)
        self.ydata_range = deque(maxlen=100)

        # Create an animation function for updating the plots
        def animate(i):
            # Fetch data from your OPS module
            data = ops_get_speed()
            if data:
                # Update current velocity and range display
                current_velocity = data.get('speed', 0)
                current_range = data.get('range', 0)
                self.current_values_text.SetLabel(f'Current Velocity: {current_velocity} \nCurrent Range: {current_range}')
                self.current_values_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

                # Append data to deques based on data type
                if data['type'] == 'velocity':
                    self.xdata_velocity.append(data['time'])
                    self.ydata_velocity.append(current_velocity)
                    self.line_velocity.set_data(self.xdata_velocity, self.ydata_velocity)
                    self.ax_velocity.relim()
                    self.ax_velocity.autoscale_view(True, True, True)

                elif data['type'] == 'range':
                    self.xdata_range.append(data['time'])
                    self.ydata_range.append(current_range)
                    self.line_range.set_data(self.xdata_range, self.ydata_range)
                    self.ax_range.relim()
                    self.ax_range.autoscale_view(True, True, True)

                # Return both lines to update both plots
                return self.line_velocity, self.line_range

        # Create an animation using the animation function
        self.ani = animation.FuncAnimation(self.fig, animate, interval=self.interval_time)

        # Create FigureCanvas for the common figure
        self.canvas = FigureCanvas(self.panel, -1, self.fig)

        # Create a section to display current velocity and range
        self.current_values_text = wx.StaticText(self.panel, label='Current Velocity: 0 \nCurrent Range: 0')
        self.current_values_text.SetForegroundColour(wx.Colour(0, 0, 255))  # Set text color to blue
        self.current_values_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        # Create buttons for top left corner
        self.start_recording_btn = wx.Button(self.panel, label='Start Recording')
        self.stop_recording_btn = wx.Button(self.panel, label='Stop Recording')
        self.stop_recording_btn.Disable()  # Disable the "Stop Recording" button initially

        # Bind events for start and stop recording buttons
        self.start_recording_btn.Bind(wx.EVT_BUTTON, self.start_recording)
        self.stop_recording_btn.Bind(wx.EVT_BUTTON, self.stop_recording)

        # Create a text box with a button for bottom left corner
        self.text_box = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE)
        self.send_btn = wx.Button(self.panel, label='Send')

        # Create a sizer for the left side
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.current_values_text, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.start_recording_btn, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.stop_recording_btn, 0, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.text_box, 1, wx.EXPAND | wx.ALL, 5)
        left_sizer.Add(self.send_btn, 0, wx.EXPAND | wx.ALL, 5)

        # Create a sizer for the right side
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)

        # Create a horizontal sizer for the entire panel
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(left_sizer, 1, wx.EXPAND)
        main_sizer.Add(right_sizer, 2, wx.EXPAND)

        self.panel.SetSizerAndFit(main_sizer)

        self.Show()

    def start_recording(self, event):
        self.recording = True
        self.start_recording_btn.Disable()
        self.stop_recording_btn.Enable()

        # Generate a unique filename based on timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'recorded_data_{timestamp}.csv'

        # Define a function for recording data and updating plot
        def record_and_update():
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Time', 'Velocity', 'Range'])

                while self.recording:
                    try:
                        data = ops_get_speed()
                        if data:
                            if data['type'] == 'velocity':
                                writer.writerow([data['time'], data['speed'], 0])
                            elif data['type'] == 'range':
                                writer.writerow([data['time'], 0, data['range']])

                            # Update plot
                            current_velocity = data.get('speed', 0)
                            current_range = data.get('range', 0)
                            self.current_values_text.SetLabel(f'Current Velocity: {current_velocity} \nCurrent Range: {current_range}')
                            self.current_values_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

                            if data['type'] == 'velocity':
                                self.xdata_velocity.append(data['time'])
                                self.ydata_velocity.append(current_velocity)
                                self.line_velocity.set_data(self.xdata_velocity, self.ydata_velocity)
                                self.ax_velocity.relim()
                                self.ax_velocity.autoscale_view(True, True, True)
                            elif data['type'] == 'range':
                                self.xdata_range.append(data['time'])
                                self.ydata_range.append(current_range)
                                self.line_range.set_data(self.xdata_range, self.ydata_range)
                                self.ax_range.relim()
                                self.ax_range.autoscale_view(True, True, True)

                            self.canvas.draw()

                        time.sleep(self.interval_time)
                    except:
                        continue

        # Start recording and updating plot in a single thread
        self.recording_thread = threading.Thread(target=record_and_update)
        self.recording_thread.start()

    def stop_recording(self, event):
        self.recording = False
        self.stop_recording_btn.Disable()
        self.start_recording_btn.Enable()
        # Join the recording thread to wait for it to finish
        if hasattr(self, 'recording_thread') and self.recording_thread.is_alive():
            self.recording_thread.join()


if __name__ == '__main__':
    app = wx.App()
    RealTimePlot(None, title='Real-Time Plot')
    app.MainLoop()
