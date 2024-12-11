# apps/stations/services/ticket_service.py

def calculate_ticket_price(start_station, end_station):
    """
    Calculate the ticket price based on the number of stations between start and end.
    Handles single-line routes and multi-line transfers.
    """
    try:
        # Validate inputs
        if not start_station or not end_station:
            raise ValueError("Both start_station and end_station must be provided.")

        # Determine total stations between start and end
        total_stations = calculate_total_stations(start_station, end_station)

        # Calculate the ticket price based on the number of stations
        return calculate_price(total_stations)

    except Exception as e:
        # Return a structured error response for better debugging
        return {"error": f"Failed to calculate ticket price: {str(e)}"}

def calculate_total_stations(start_station, end_station):
    """
    Calculate the total number of stations between start and end stations.
    Handles single-line and multi-line scenarios.
    """
    start_lines = start_station.lines.all()
    end_lines = end_station.lines.all()

    if not start_lines or not end_lines:
        raise ValueError("Start or end station is not part of any line.")

    # Case 1: Single line (direct route)
    if set(start_lines) == set(end_lines):
        start_line = start_lines.first()
        start_order = start_station.get_station_order(start_line)
        end_order = end_station.get_station_order(start_line)
        return abs(end_order - start_order) + 1

    # Case 2: Multi-line (transfer required)
    return calculate_transfer_cost(start_station, end_station)

def calculate_transfer_cost(start_station, end_station):
    """
    Calculate the total stations for routes requiring a transfer.
    Assumes a simplified model with direct transfers via interchange stations.
    """
    # Simulate transfer via an interchange station (e.g., central station logic)
    # Extend this logic to handle complex transfer scenarios
    start_line = start_station.lines.first()
    end_line = end_station.lines.first()

    start_order = start_station.get_station_order(start_line)
    end_order = end_station.get_station_order(end_line)

    # Add logic for actual interchange station determination if required
    return abs(end_order - start_order) + 1

def calculate_price(station_count):
    """
    Determine ticket price based on the number of stations.
    """
    if station_count <= 9:
        return 8  # EGP
    elif station_count <= 16:
        return 10  # EGP
    elif station_count <= 23:
        return 15  # EGP
    return 20  # EGP
