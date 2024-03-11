import time
import queue
from serial_ops import start_ops_thread

def main():
    data_queue = start_ops_thread("/dev/cu.usbmodem14201")  # Adjust the port as needed

    while True:
        try:
            data = data_queue.get(timeout=1)  # Get data from the queue with a timeout
            print("Received data:", data)
            # Process data as needed
        except queue.Empty:
            # No data available, do something else or just wait
            pass
        time.sleep(0.1)  # Optional: Adjust the delay as needed to reduce CPU load

if __name__ == "__main__":
    main()
