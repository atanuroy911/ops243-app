import serial
import json
import threading
import queue
import time

def send_serial_cmd(ser, print_prefix, command):
    """
    function for sending serial commands to the OPS module
    """
    data_for_send_str = command
    data_for_send_bytes = str.encode(data_for_send_str)
    print(print_prefix, command)
    ser.write(data_for_send_bytes)
    # initialize message verify checking
    ser_message_start = "{"
    ser_write_verify = False
    # print out module response to command string
    while not ser_write_verify:
        data_rx_bytes = ser.readline()
        data_rx_length = len(data_rx_bytes)
        if data_rx_length != 0:
            data_rx_str = str(data_rx_bytes)
            if data_rx_str.find(ser_message_start):
                ser_write_verify = True

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

def start_ops_thread(port):
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

    # Set up a queue to communicate between threads
    data_queue = queue.Queue()

    # Start the OPS worker thread
    ops_thread = threading.Thread(target=ops_worker, args=(ser, data_queue))
    ops_thread.daemon = True  # Thread will terminate when the main program exits
    ops_thread.start()

    return data_queue
