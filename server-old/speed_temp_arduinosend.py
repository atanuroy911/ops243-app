import serial

def send_serial_cmd(print_prefix, command):
    """
    Function for sending serial commands to the OPS module
    """
    data_for_send_str = command
    data_for_send_bytes = str.encode(data_for_send_str)
    print(print_prefix, command)
    ser.write(data_for_send_bytes)
    # Initialize message verify checking
    ser_message_start = "{"
    ser_write_verify = False
    # Print out module response to command string
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
    port="COM7",
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1,
    writeTimeout=2,
)

# Open serial connection to Arduino
arduino_serial = serial.Serial('COM10', 9600)  # Replace 'COM10' with appropriate port for Arduino

ser.flushInput()
ser.flushOutput()

# Constants for the OPS module
Ops_Speed_Output_Units = ["US", "UK", "UM", "UC"]
Ops_Speed_Output_Units_lbl = ["mph", "km/h", "m/s", "cm/s"]
Ops_Blanks_Pref_Zero = "BZ"
Ops_Sampling_Frequency = "SX"
Ops_Transmit_Power = "PX"
Ops_Threshold_Control = "MX"
Ops_Module_Information = "??"
Ops_Overlook_Buffer = "OZ"
Ops_Json_Output = "OJ"
Ops_Detect_Object_Output = "ON"
Ops_Time_Set = "OT"
Ops_TimeHuman_Set = "OH"
Ops_Set_Sampling_Rate = "SX"
Ops_Delayed_Report = "W4"

# Initialize the OPS module
send_serial_cmd("\nOverlook buffer", Ops_Overlook_Buffer)
send_serial_cmd("\nSet Speed Output Units: ", Ops_Speed_Output_Units[1])
send_serial_cmd("\nSet Sampling Frequency: ", Ops_Sampling_Frequency)
send_serial_cmd("\nSet Transmit Power: ", Ops_Transmit_Power)
send_serial_cmd("\nSet Threshold Control: ", Ops_Threshold_Control)
send_serial_cmd("\nSet Blanks Preference: ", Ops_Blanks_Pref_Zero)
send_serial_cmd("\nSet Json Preference: ", Ops_Json_Output)
send_serial_cmd("\nSet Sampling Preference: ", Ops_Set_Sampling_Rate)
send_serial_cmd("\nSet Time Preference: ", Ops_Time_Set)
# send_serial_cmd("\nSet Detect Object Preference: ", Ops_Detect_Object_Output)
send_serial_cmd("\nSet Report delay Preference: ", Ops_Delayed_Report)

def ops_get_speed():
    """
    Capture speed reading from OPS module and send to Arduino
    """
    while True:
        speed_available = False
        Ops_rx_bytes = ser.readline()
        # Check for speed information from OPS module
        Ops_rx_bytes_length = len(Ops_rx_bytes)
        # Process the streaming data line by line
        
        strip_data = Ops_rx_bytes.decode("utf-8").strip()
        data = strip_data.split(',')  # Split the received data into a list
        print(data)
        # Send data to Arduino
        send_data_to_arduino(data)

ops_get_speed()
