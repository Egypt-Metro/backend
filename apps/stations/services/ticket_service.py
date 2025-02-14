# apps/stations/services/ticket_service.py


from venv import logger


def calculate_total_stations(start_station, end_station, route_path=None):
    """
    Calculate total stations including interchanges.
    """
    if not route_path:
        return 0

    # Count unique stations in path
    unique_stations = set()
    for station in route_path:
        unique_stations.add(station['station'])

    return len(unique_stations)


def calculate_ticket_price(start_station, end_station, route_path=None):
    """Calculate ticket price based on total stations and interchanges"""
    try:
        if not route_path:
            return None

        # Count unique stations
        stations = set()
        prev_line = None
        transfers = 0

        for segment in route_path:
            stations.add(segment['station'])
            if prev_line and segment['line'] != prev_line:
                transfers += 1
            prev_line = segment['line']

        total_stations = len(stations)

        # Base price based on stations
        if total_stations <= 9:
            price = 8
        elif total_stations <= 16:
            price = 10
        elif total_stations <= 23:
            price = 15
        else:
            price = 20

        # Add transfer fee
        price += (transfers * 2)  # 2 EGP per transfer

        return price

    except Exception as e:
        logger.error(f"Error calculating ticket price: {str(e)}")
        raise


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
