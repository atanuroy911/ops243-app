import serial
import json
import threading
import queue
import time

def ops_worker(ser, data_queue):
    """
    Worker function to capture speed reading from OPS module
    """
    while True:
        Ops_rx_bytes = ser.readline()
        strip_data = Ops_rx_bytes.decode("utf-8").strip()
        try:
            data = json.loads(strip_data)
            data_queue.put(data)
        except json.JSONDecodeError:
            print("Error decoding JSON:", strip_data)
            continue

def start_ops_thread(port):
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
            print(ser_write_verify)
            
    ser = serial.Serial(
        port=port,
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1,
        writeTimeout=2,
    )
    ser.flushInput()
    ser.flushOutput()
    
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
    Ops_Detect_Object_Output = "ON"
    Ops_Time_Set = "OT"
    Ops_TimeHuman_Set = "OH"
    Ops_Set_Sampling_Rate = "SX"
    # Ops_Delayed_Report = "W1"

    # initialize the OPS module
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
    # send_serial_cmd("\nSet Report delay Preference: ", Ops_Delayed_Report)
    
    time.sleep(1)
    # Set up a queue to communicate between threads
    data_queue = queue.Queue()

    # Start the OPS worker thread
    ops_thread = threading.Thread(target=ops_worker, args=(ser, data_queue))
    ops_thread.daemon = True  # Thread will terminate when the main program exits
    ops_thread.start()

    return data_queue
