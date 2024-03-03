# Real-time Radar Data Visualization with Flask and Chart.js

This repository demonstrates a real-time data visualization application for the Omnipresense 243-C Radar using Flask, Chart.js, and WebSocket communication. It includes a Flask server to receive data from the radar via WebSocket and a client-side Chart.js chart to visualize the real-time radar data.

## Requirements

- Python (3.6 or higher)
- Flask
- Flask-Sockets
- Chart.js
- WebSocket-enabled browser
- Omnipresense 243-C Radar hardware

## Installation

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/your-username/real-time-radar-visualization.git
    ```

2. Install the required Python packages using pip:

    ```bash
    pip install Flask Flask-Sockets
    ```

3. Include Chart.js in your HTML page. You can use a CDN link or download Chart.js and include it locally.

## Usage

1. Connect the Omnipresense 243-C Radar to your computer.

2. Run the Flask server to start receiving data from the radar and serving the web page:

    ```bash
    python app.py
    ```

3. Open your web browser and navigate to `http://localhost:5000` to view the real-time radar data visualization.

4. Data received from the radar will be visualized in real-time on the chart.

## Configuration

- Modify `app.py` to adjust the WebSocket endpoint and radar settings as needed.

- Customize the Chart.js chart options in the client-side JavaScript code (`templates/index.html`) to meet your visualization requirements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
