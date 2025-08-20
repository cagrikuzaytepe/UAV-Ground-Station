# UAV Control Application

## Project Overview

The UAV Control Application is a comprehensive system designed for controlling Unmanned Aerial Vehicles (UAVs). It provides dual interfaces for interaction: a user-friendly Graphical User Interface (GUI) for manual control and real-time monitoring, and a robust RESTful API for programmatic control, automation, and integration with other systems. This application aims to offer a flexible and powerful solution for various UAV operations, from simple flight commands to complex mission planning.

## Features

*   **Intuitive Graphical User Interface (GUI):**
    *   Real-time telemetry display (altitude, speed, GPS coordinates, battery status).
    *   Manual flight control commands (takeoff, land, move to specific coordinates).
    *   Mission planning and execution capabilities.
*   **Robust RESTful API:**
    *   Programmatic control over UAVs, enabling integration with external applications and scripts.
    *   Endpoints for essential flight operations: connect, arm, takeoff, land, goto, set mode, and telemetry retrieval.
    *   Standardized JSON-based communication for easy parsing and interaction.
*   **Modular Architecture:**
    *   Separation of concerns with dedicated modules for API, GUI, and core drone control logic.
    *   Facilitates easy maintenance, scalability, and future enhancements.
*   **Core Drone Control Logic:**
    *   Abstracted control layer for various drone operations, ensuring consistent behavior.
    *   Handles communication with the drone hardware/simulator.

## Installation

To set up the UAV Control Application, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/uav_control_app.git
    cd uav_control_app
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running the GUI Application

To start the graphical user interface:

```bash
python src/main.py
```

This will launch the main window, allowing you to connect to a drone and issue commands through the GUI.

### Running the API Server

To start the RESTful API server:

```bash
uvicorn src.api.endpoints:app --host 0.0.0.0 --port 8000
```

The API server will be accessible at `http://0.0.0.0:8000`.

## API Endpoints

The API provides the following endpoints for controlling the UAV:

### `POST /connect`

Connects to the drone.

*   **Request Body:**
    ```json
    {
      "connection_string": "tcp:127.0.0.1:5760"
    }
    ```
*   **Response:**
    ```json
    {
      "status": "success",
      "message": "Connected to drone"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to connect"
    }
    ```

### `POST /arm`

Arms the drone.

*   **Response:**
    ```json
    {
      "status": "success",
      "message": "Drone armed"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to arm"
    }
    ```

### `POST /takeoff`

Commands the drone to take off to a specified altitude.

*   **Request Body:**
    ```json
    {
      "altitude": 10
    }
    ```
*   **Response:**
    ```json
    {
      "status": "success",
      "message": "Drone taking off"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to takeoff"
    }
    ```

### `POST /land`

Commands the drone to land.

*   **Response:**
    ```json
    {
      "status": "success",
      "message": "Drone landing"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to land"
    }
    ```

### `POST /goto`

Commands the drone to fly to a specific GPS location.

*   **Request Body:**
    ```json
    {
      "latitude": 34.0,
      "longitude": -118.0,
      "altitude": 50
    }
    ```
*   **Response:**
    ```json
    {
      "status": "success",
      "message": "Drone moving to target location"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to move"
    }
    ```

### `POST /set_mode`

Sets the flight mode of the drone.

*   **Request Body:**
    ```json
    {
      "mode": "GUIDED"
    }
    ```
*   **Response:**
    ```json
    {
      "status": "success",
      "message": "Flight mode set to GUIDED"
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to set mode"
    }
    ```

### `GET /get_telemetry`

Retrieves the current telemetry data from the drone.

*   **Response:**
    ```json
    {
      "latitude": 34.0,
      "longitude": -118.0,
      "altitude": 50.0,
      "groundspeed": 5.0,
      "airspeed": 5.0,
      "heading": 90,
      "battery_voltage": 12.5,
      "battery_current": 10.0,
      "battery_level": 80
    }
    ```
    or
    ```json
    {
      "status": "error",
      "message": "Failed to retrieve telemetry"
    }
    ```

## Testing

To run the unit tests for the application:

```bash
python -m unittest discover tests
```

This command will discover and run all tests located in the `tests/` directory.

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add new feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Create a Pull Request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
