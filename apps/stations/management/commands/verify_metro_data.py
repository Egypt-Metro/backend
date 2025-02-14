# verify_metro_data.py
from apps.stations.models import Line, Station, LineStation
from apps.stations.management.commands.populate_metro_data import Command as MetroDataCommand


def verify_metro_system():
    """Verify the metro system data"""
    print("\nVerifying Metro System Data...")

    # Check Lines
    lines = Line.objects.all()
    print(f"\nLines ({lines.count()}):")
    for line in lines:
        stations = line.stations.count()
        print(f"- {line.name}: {stations} stations")

        # Verify station order
        line_stations = LineStation.objects.filter(line=line).order_by('order')
        print("  Station order:")
        for ls in line_stations:
            print(f"    {ls.order}. {ls.station.name}")

    # Check Connecting Stations
    print("\nVerifying Interchange Stations:")
    for conn in MetroDataCommand.CONNECTING_STATIONS:
        station = Station.objects.filter(name=conn["name"]).first()
        if station:
            actual_lines = set(line.name for line in station.lines.all())
            expected_lines = set(conn["lines"])
            if actual_lines == expected_lines:
                print(f"✓ {station.name}: Correct connections")
            else:
                print(f"✗ {station.name}: Connection mismatch")
                print(f"  Expected: {expected_lines}")
                print(f"  Found: {actual_lines}")
        else:
            print(f"✗ {conn['name']}: Station not found")

    # Check Third Line Branches
    print("\nVerifying Third Line Branches:")
    third_line = Line.objects.get(name="Third Line")

    # Check main branch
    main_branch_stations = LineStation.objects.filter(
        line=third_line,
        order__lt=1000  # Main branch stations have normal order
    ).order_by('order')

    print(f"Main Branch ({main_branch_stations.count()} stations):")
    for ls in main_branch_stations:
        print(f"  {ls.order}. {ls.station.name}")

    # Check secondary branch
    branch_stations = LineStation.objects.filter(
        line=third_line,
        order__gte=1000  # Branch stations have order 1000+
    ).order_by('order')

    print(f"\nCairo University Branch ({branch_stations.count()} stations):")
    for ls in branch_stations:
        print(f"  {ls.order}. {ls.station.name}")


if __name__ == "__main__":
    verify_metro_system()
