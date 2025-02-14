# apps/stations/tests.py
from django.test import TestCase
from .models import Line, Station, LineStation
from .management.commands.populate_metro_data import Command as MetroDataCommand


class MetroSystemTests(TestCase):
    def setUp(self):
        # Populate test data
        command = MetroDataCommand()
        command.handle()

    def test_line_counts(self):
        """Test that we have the correct number of lines"""
        self.assertEqual(Line.objects.count(), 3)

    def test_station_counts(self):
        """Test station counts for each line"""
        first_line = Line.objects.get(name="First Line")
        second_line = Line.objects.get(name="Second Line")
        third_line = Line.objects.get(name="Third Line")

        self.assertEqual(first_line.stations.count(), 35)
        self.assertEqual(second_line.stations.count(), 20)
        self.assertEqual(third_line.stations.count(), 34)

    def test_connecting_stations(self):
        """Test that connecting stations are properly set up"""
        for conn in MetroDataCommand.CONNECTING_STATIONS:
            station = Station.objects.get(name=conn["name"])
            self.assertTrue(station.is_interchange())
            self.assertEqual(
                set(line.name for line in station.lines.all()),
                set(conn["lines"])
            )

    def test_third_line_branches(self):
        """Test that Third Line branches are properly set up"""
        third_line = Line.objects.get(name="Third Line")
        branch_point = Station.objects.get(name="Kit Kat")

        # Check branch point
        self.assertTrue(
            LineStation.objects.filter(
                line=third_line,
                station=branch_point
            ).exists()
        )

        # Check branch stations
        branch_stations = LineStation.objects.filter(
            line=third_line,
            order__gte=1000
        )
        self.assertTrue(branch_stations.exists())
