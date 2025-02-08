# apps/routes/utils/validation.py

def is_valid_station_id(station_id):
    """
    Ensures station ID is a positive integer.
    """
    return isinstance(station_id, int) and station_id > 0
