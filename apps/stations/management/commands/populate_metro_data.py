# apps/stations/management/commands/populate_metro_data.py

import time
from venv import logger
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stations.models import Line, Station, LineStation, ConnectingStation
from django.db import connection
from django.db.models import Q


class Command(BaseCommand):
    help = "Populate metro lines, stations, and connections data"

    # Metro data definitions
    METRO_DATA = [
        {
            "line": {"name": "First Line", "color_code": "#FF0000"},
            "stations": [
                {"name": "Helwan", "latitude": 29.849, "longitude": 31.334},
                {"name": "Ain Helwan", "latitude": 29.851, "longitude": 31.319},
                {"name": "Helwan University", "latitude": 29.868, "longitude": 31.320},
                {"name": "Wadi Hof", "latitude": 29.879, "longitude": 31.313},
                {"name": "Hadayek Helwan", "latitude": 29.897, "longitude": 31.304},
                {"name": "El-Maasara", "latitude": 29.906, "longitude": 31.299},
                {"name": "Tora El-Asmant", "latitude": 29.926, "longitude": 31.288},
                {"name": "Kozzika", "latitude": 29.936, "longitude": 31.281},
                {"name": "Tora El-Balad", "latitude": 29.947, "longitude": 31.274},
                {"name": "Sakanat El-Maadi", "latitude": 29.953, "longitude": 31.264},
                {"name": "Maadi", "latitude": 29.957, "longitude": 31.257},
                {"name": "Hadayek El-Maadi", "latitude": 29.970, "longitude": 31.250},
                {"name": "Dar El-Salam", "latitude": 29.981, "longitude": 31.242},
                {"name": "El-Zahraa'", "latitude": 29.995, "longitude": 31.231},
                {"name": "Mar Girgis", "latitude": 30.006, "longitude": 31.230},
                {"name": "El-Malek El-Saleh", "latitude": 30.017, "longitude": 31.231},
                {"name": "Al-Sayeda Zeinab", "latitude": 30.029, "longitude": 31.235},
                {"name": "Saad Zaghloul", "latitude": 30.037, "longitude": 31.237},
                {"name": "Sadat", "latitude": 30.044, "longitude": 31.235},
                {"name": "Nasser", "latitude": 30.053, "longitude": 31.240},
                {"name": "Orabi", "latitude": 30.057, "longitude": 31.243},
                {"name": "Al-Shohadaa", "latitude": 30.060, "longitude": 31.248},
                {"name": "Ghamra", "latitude": 30.068, "longitude": 31.265},
                {"name": "El-Demerdash", "latitude": 30.078, "longitude": 31.277},
                {"name": "Manshiet El-Sadr", "latitude": 30.082, "longitude": 31.288},
                {"name": "Kobri El-Qobba", "latitude": 30.087, "longitude": 31.294},
                {"name": "Hammamat El-Qobba", "latitude": 30.090, "longitude": 31.298},
                {"name": "Saray El-Qobba", "latitude": 30.098, "longitude": 31.303},
                {"name": "Hadayek El-Zaitoun", "latitude": 30.105, "longitude": 31.310},
                {"name": "Helmeyet El-Zaitoun", "latitude": 30.115, "longitude": 31.314},
                {"name": "El-Matareyya", "latitude": 30.121, "longitude": 31.315},
                {"name": "Ain Shams", "latitude": 30.131, "longitude": 31.318},
                {"name": "Ezbet El-Nakhl", "latitude": 30.139, "longitude": 31.324},
                {"name": "El-Marg", "latitude": 30.151, "longitude": 31.335},
                {"name": "New El-Marg", "latitude": 30.163, "longitude": 31.337},
            ],
        },
        {
            "line": {"name": "Second Line", "color_code": "#008000"},
            "stations": [
                {"name": "El-Mounib", "latitude": 29.98139, "longitude": 31.21194},
                {"name": "Sakiat Mekky", "latitude": 29.99556, "longitude": 31.20861},
                {"name": "Omm El-Masryeen", "latitude": 30.00528, "longitude": 31.20806},
                {"name": "El Giza", "latitude": 30.01056, "longitude": 31.20722},
                {"name": "Faisal", "latitude": 30.01722, "longitude": 31.20389},
                {"name": "Cairo University", "latitude": 30.02611, "longitude": 31.20111},
                {"name": "El Bohoth", "latitude": 30.03583, "longitude": 31.20028},
                {"name": "Dokki", "latitude": 30.03833, "longitude": 31.21194},
                {"name": "Opera", "latitude": 30.04222, "longitude": 31.22528},
                {"name": "Sadat", "latitude": 30.04444, "longitude": 31.23556},
                {"name": "Mohamed Naguib", "latitude": 30.04528, "longitude": 31.24417},
                {"name": "Attaba", "latitude": 30.05250, "longitude": 31.24722},
                {"name": "Al-Shohadaa", "latitude": 30.06000, "longitude": 31.24800},
                {"name": "Masarra", "latitude": 30.07111, "longitude": 31.24500},
                {"name": "Road El-Farag", "latitude": 30.08056, "longitude": 31.24556},
                {"name": "St. Teresa", "latitude": 30.08833, "longitude": 31.24556},
                {"name": "Khalafawy", "latitude": 30.09806, "longitude": 31.24528},
                {"name": "Mezallat", "latitude": 30.10500, "longitude": 31.24667},
                {"name": "Kolleyyet El-Zeraa", "latitude": 30.11389, "longitude": 31.24861},
                {"name": "Shubra El-Kheima", "latitude": 30.12250, "longitude": 31.24472},
            ],
        },
        {
            "line": {"name": "Third Line", "color_code": "#0000FF"},
            "main_branch": {
                "name": "Main Branch",
                "stations": [
                    # Eastern Branch (Adly Mansour to Kit Kat)
                    {"name": "Adly Mansour", "latitude": 30.147194, "longitude": 31.421528},
                    {"name": "El Haykestep", "latitude": 30.143889, "longitude": 31.404722},
                    {"name": "Omar Ibn El-Khattab", "latitude": 30.140556, "longitude": 31.394167},
                    {"name": "Qobaa", "latitude": 30.134722, "longitude": 31.383889},
                    {"name": "Hesham Barakat", "latitude": 30.131111, "longitude": 31.373889},
                    {"name": "El-Nozha", "latitude": 30.128333, "longitude": 31.360000},
                    {"name": "Nadi El-Shams", "latitude": 30.122222, "longitude": 31.343889},
                    {"name": "Alf Maskan", "latitude": 30.118056, "longitude": 31.339722},
                    {"name": "Heliopolis Square", "latitude": 30.108056, "longitude": 31.337222},
                    {"name": "Haroun", "latitude": 30.100000, "longitude": 31.332778},
                    {"name": "Al-Ahram", "latitude": 30.091389, "longitude": 31.326389},
                    {"name": "Koleyet El-Banat", "latitude": 30.083611, "longitude": 31.328889},
                    {"name": "Stadium", "latitude": 30.073056, "longitude": 31.317500},
                    {"name": "Fair Zone", "latitude": 30.073333, "longitude": 31.301111},
                    {"name": "Abbassia", "latitude": 30.069722, "longitude": 31.280833},
                    {"name": "Abdou Pasha", "latitude": 30.064722, "longitude": 31.274722},
                    {"name": "El Geish", "latitude": 30.062222, "longitude": 31.266944},
                    {"name": "Bab El Shaaria", "latitude": 30.053889, "longitude": 31.256111},
                    {"name": "Attaba", "latitude": 30.052500, "longitude": 31.247222},
                    {"name": "Nasser", "latitude": 30.053611, "longitude": 31.236111},
                    {"name": "Maspero", "latitude": 30.055556, "longitude": 31.232222},
                    {"name": "Safaa Hegazy", "latitude": 30.062500, "longitude": 31.223611},
                    {"name": "Kit Kat", "latitude": 30.066667, "longitude": 31.212500},
                    # Northern Extension (Kit Kat to Rod al-Farag Axis)
                    {"name": "Sudan Street", "latitude": 30.069722, "longitude": 31.204722},
                    {"name": "Imbaba", "latitude": 30.075833, "longitude": 31.207500},
                    {"name": "El-Bohy", "latitude": 30.082222, "longitude": 31.210556},
                    {"name": "Al-Qawmeya Al-Arabiya", "latitude": 30.093333, "longitude": 31.208889},
                    {"name": "Ring Road", "latitude": 30.096389, "longitude": 31.199722},
                    {"name": "Rod al-Farag Axis", "latitude": 30.101944, "longitude": 31.184167}
                ]
            },
            "branch": {
                "name": "Cairo University Branch",
                "branch_point": "Kit Kat",
                "stations": [
                    # Southern Branch (Kit Kat to Cairo University)
                    {"name": "Kit Kat", "latitude": 30.066667, "longitude": 31.212500},
                    {"name": "El-Tawfikeya", "latitude": 30.065278, "longitude": 31.202500},
                    {"name": "Wadi El-Nil", "latitude": 30.058333, "longitude": 31.200000},
                    {"name": "Gamaat El Dowal Al-Arabiya", "latitude": 30.050833, "longitude": 31.199722},
                    {"name": "Bulaq El-Dakroor", "latitude": 30.036111, "longitude": 31.196389},
                    {"name": "Cairo University", "latitude": 30.026111, "longitude": 31.201111}
                ]
            }
        },
    ]

    # Define branch information
    BRANCH_INFO = {
        "Third Line": {
            "main_branch": {
                "start": "Adly Mansour",
                "end": "Rod al-Farag Axis",
                "branch_point": "Kit Kat",
                "sections": [
                    {"start": "Adly Mansour", "end": "Kit Kat"},
                    {"start": "Kit Kat", "end": "Rod al-Farag Axis"}
                ]
            },
            "secondary_branch": {
                "start": "Kit Kat",
                "end": "Cairo University",
                "connection_point": "Kit Kat"
            }
        }
    }

    # Define line directions
    LINE_DIRECTIONS = {
        "First Line": {"start": "Helwan", "end": "New El-Marg"},
        "Second Line": {"start": "El-Mounib", "end": "Shubra El-Kheima"},
        "Third Line": {"start": "Adly Mansour", "end": "Rod al-Farag Axis"}
    }

    CONNECTING_STATIONS = [
        {
            "name": "Sadat",
            "lines": ["First Line", "Second Line"],
            "transfer_time": 3  # minutes
        },
        {
            "name": "Nasser",
            "lines": ["First Line", "Third Line"],
            "transfer_time": 3
        },
        {
            "name": "Al-Shohadaa",
            "lines": ["First Line", "Second Line"],
            "transfer_time": 3
        },
        {
            "name": "Attaba",
            "lines": ["Second Line", "Third Line"],
            "transfer_time": 3
        },
        {
            "name": "Cairo University",
            "lines": ["Second Line", "Third Line"],
            "transfer_time": 3
        }
    ]

    LINE_OPERATIONS = {
        "First Line": {
            "weekday": {"first_train": "09:00", "last_train": "00:00"},  # 12 AM
            "weekend": {"first_train": "09:00", "last_train": "22:00"},  # 10 PM
        },
        "Second Line": {
            "weekday": {"first_train": "09:00", "last_train": "00:00"},
            "weekend": {"first_train": "09:00", "last_train": "22:00"},
        },
        "Third Line": {
            "weekday": {"first_train": "09:00", "last_train": "00:00"},
            "weekend": {"first_train": "09:00", "last_train": "22:00"},
        }
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information'
        )

    def log_performance(self, operation_start, operation_name):
        """Log performance metrics"""
        duration = time.time() - operation_start
        query_count = len(connection.queries)
        self.stdout.write(f"{operation_name} completed in {duration:.2f}s with {query_count} queries")

    def validate_metro_data(self):
        """Validate metro data before population"""
        try:
            # Validate line data
            for line_data in self.METRO_DATA:
                # Check line has required fields
                if not all(key in line_data["line"] for key in ["name", "color_code"]):
                    raise ValueError(f"Missing required fields in line data: {line_data['line']}")

                # Check stations have required coordinates
                for station in line_data["stations"]:
                    if not all(key in station for key in ["name", "latitude", "longitude"]):
                        raise ValueError(f"Missing coordinates for station: {station['name']}")

                    # Validate coordinates
                    if not (-90 <= station["latitude"] <= 90) or not (-180 <= station["longitude"] <= 180):
                        raise ValueError(f"Invalid coordinates for station: {station['name']}")

            # Validate connecting stations
            station_names = {
                station["name"]
                for line in self.METRO_DATA
                for station in line["stations"]
            }

            for conn in self.CONNECTING_STATIONS:
                if conn["name"] not in station_names:
                    raise ValueError(f"Connecting station not found: {conn['name']}")

                for line_name in conn["lines"]:
                    if not any(line["line"]["name"] == line_name for line in self.METRO_DATA):
                        raise ValueError(f"Invalid line in connecting station: {line_name}")

            logger.info("Metro data validation passed")
            return True

        except Exception as e:
            logger.error(f"Metro data validation failed: {str(e)}")
            raise

    def verify_station_order(self):
        """Verify stations are in correct order according to the map"""
        for line_data in self.METRO_DATA:
            line_name = line_data["line"]["name"]
            stations = line_data["stations"]

            # Verify direction matches LINE_DIRECTIONS
            direction = self.LINE_DIRECTIONS[line_name]
            if stations[0]["name"] != direction["start"] or stations[-1]["name"] != direction["end"]:
                raise ValueError(f"Station order mismatch for {line_name}")

            # For Third Line, verify branch structure
            if line_name == "Third Line":
                branch_info = self.BRANCH_INFO["Third Line"]
                # main_branch variable removed as it was not used

                # Verify branch point exists
                if branch_info["main_branch"]["branch_point"] not in [s["name"] for s in stations]:
                    raise ValueError("Branch point station not found")

    @transaction.atomic
    def handle(self, *args, **kwargs):
        start_time = time.time()  # Use time.time() for performance measurement
        try:
            self.stdout.write("Starting metro data population...")

            # Clear existing data
            clear_start = time.time()
            self.clear_existing_data()
            duration = time.time() - clear_start
            self.stdout.write(f"Data clearing completed in {duration:.2f}s")

            # Create lines
            lines_start = time.time()
            self.create_lines()
            duration = time.time() - lines_start
            self.stdout.write(f"Line creation completed in {duration:.2f}s")

            # Create stations
            stations_start = time.time()
            self.create_stations()
            duration = time.time() - stations_start
            self.stdout.write(f"Station creation completed in {duration:.2f}s")

            # Create connecting stations
            connections_start = time.time()
            self.create_connecting_stations()
            duration = time.time() - connections_start
            self.stdout.write(f"Connection creation completed in {duration:.2f}s")

            # Verify data integrity
            verify_start = time.time()
            verification_results = self.verify_data_integrity()
            duration = time.time() - verify_start
            self.stdout.write(f"Data verification completed in {duration:.2f}s")

            # Print verification results
            self.stdout.write("\nVerification Results:")
            self.stdout.write(f"Lines: {verification_results['lines']}")
            self.stdout.write(f"Stations: {verification_results['stations']}")
            self.stdout.write(f"Connections: {verification_results['connections']}")
            self.stdout.write(f"LineStations: {verification_results['line_stations']}")

            # Calculate total time
            total_duration = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nMetro data population completed successfully in {total_duration:.2f}s"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error populating metro data: {str(e)}")
            )
            raise

    def clear_existing_data(self):
        """Clear all existing metro data"""
        self.stdout.write("Clearing existing data...")
        LineStation.objects.all().delete()
        ConnectingStation.objects.all().delete()
        Station.objects.all().delete()
        Line.objects.all().delete()

    def create_lines(self):
        """Create metro lines"""
        for line_data in self.METRO_DATA:
            line, created = Line.objects.get_or_create(
                name=line_data["line"]["name"],
                defaults={
                    "color_code": line_data["line"]["color_code"],
                }
            )
            self.stdout.write(f"{'Created' if created else 'Updated'} line: {line.name}")

    def create_stations(self):
        """Create stations and their connections"""
        for line_data in self.METRO_DATA:
            line = Line.objects.get(name=line_data["line"]["name"])

            if line.name == "Third Line":
                # Handle Third Line's special structure with main branch and secondary branch
                # Main branch stations
                order = 1
                for station_data in line_data["main_branch"]["stations"]:
                    station, created = Station.objects.get_or_create(
                        name=station_data["name"],
                        defaults={
                            "latitude": station_data["latitude"],
                            "longitude": station_data["longitude"]
                        }
                    )

                    LineStation.objects.get_or_create(
                        line=line,
                        station=station,
                        defaults={"order": order}
                    )
                    order += 1

                # Branch stations (starting from 1000 to distinguish from main line)
                branch_order = 1000
                for station_data in line_data["branch"]["stations"]:
                    # Skip Kit Kat as it's already created in main branch
                    if station_data["name"] != "Kit Kat":
                        station, created = Station.objects.get_or_create(
                            name=station_data["name"],
                            defaults={
                                "latitude": station_data["latitude"],
                                "longitude": station_data["longitude"]
                            }
                        )

                        LineStation.objects.get_or_create(
                            line=line,
                            station=station,
                            defaults={"order": branch_order}
                        )
                        branch_order += 1
            else:
                # Handle regular lines (First and Second Lines)
                order = 1
                for station_data in line_data["stations"]:
                    station, created = Station.objects.get_or_create(
                        name=station_data["name"],
                        defaults={
                            "latitude": station_data["latitude"],
                            "longitude": station_data["longitude"]
                        }
                    )

                    LineStation.objects.get_or_create(
                        line=line,
                        station=station,
                        defaults={"order": order}
                    )
                    order += 1

            self.stdout.write(f"Created/Updated stations for {line.name}")

    def create_connecting_stations(self):
        """Create connecting stations between lines"""
        for conn_data in self.CONNECTING_STATIONS:
            station = Station.objects.get(name=conn_data["name"])
            connecting_station, _ = ConnectingStation.objects.get_or_create(
                station=station,
                defaults={"transfer_time": conn_data["transfer_time"]}
            )

            # Add connections to lines
            for line_name in conn_data["lines"]:
                line = Line.objects.get(name=line_name)
                connecting_station.lines.add(line)

    def validate_data(self):
        """Validate the populated data"""
        for line_name, direction in self.LINE_DIRECTIONS.items():
            line = Line.objects.get(name=line_name)
            stations = line.get_stations_in_order()

            if not stations:
                raise ValueError(f"No stations found for {line_name}")

            if stations[0].name != direction["start"]:
                raise ValueError(f"First station of {line_name} should be {direction['start']}")

            if stations[-1].name != direction["end"]:
                raise ValueError(f"Last station of {line_name} should be {direction['end']}")

    def populate_lines_and_stations(self):
        """Populate the metro lines and stations."""
        self.stdout.write("Populating metro lines and stations...")
        for line_data in self.METRO_DATA:
            line, created = Line.objects.update_or_create(
                name=line_data["line"]["name"],
                defaults={"color_code": line_data["line"].get("color_code")},
            )

            # Get branch information if exists
            branch_info = next(
                (b for b in self.BRANCH_POINTS if b["line"] == line.name),
                None
            )

            for order, station_data in enumerate(line_data["stations"], start=1):
                station, created = Station.objects.update_or_create(
                    name=station_data["name"],
                    defaults={
                        "latitude": station_data.get("latitude"),
                        "longitude": station_data.get("longitude"),
                    },
                )

                # Handle branch ordering
                if branch_info and station.name in branch_info["secondary_branch"]:
                    # Adjust order for branch stations
                    branch_order = branch_info["secondary_branch"].index(station.name)
                    order = 1000 + branch_order  # Use high numbers for branch stations

                line_station, ls_created = LineStation.objects.update_or_create(
                    line=line,
                    station=station,
                    defaults={"order": order}
                )

    def handle_third_line_branch(self, line, branch_point_station, main_order):
        """Handle the Third Line branch to Cairo University"""
        branch_stations = [
            station for station in self.METRO_DATA[2]["stations"]
            if station["name"] in ["Cairo University", "Bulaq El-Dakroor",
                                   "Gamaat El Dowal Al-Arabiya", "Wadi El-Nil", "El-Tawfikeya"]
        ]

        # Use high order numbers for branch stations to distinguish them
        branch_order = 1000
        for station_data in branch_stations:
            station, _ = Station.objects.get_or_create(
                name=station_data["name"],
                defaults={
                    "latitude": station_data["latitude"],
                    "longitude": station_data["longitude"]
                }
            )

            LineStation.objects.get_or_create(
                line=line,
                station=station,
                defaults={"order": branch_order}
            )
            branch_order += 1

    def populate_connecting_stations(self):
        """Populate connecting stations between lines."""
        for conn_station in self.CONNECTING_STATIONS:
            station = Station.objects.get(name=conn_station["name"])

            lines = Line.objects.filter(name__in=conn_station["lines"])
            for line in lines:
                # Check if the ConnectingStation already exists
                if not ConnectingStation.objects.filter(
                    station=station, lines=line
                ).exists():
                    (
                        connecting_station,
                        created,
                    ) = ConnectingStation.objects.get_or_create(station=station)
                    connecting_station.lines.add(line)
                    action = "Created" if created else "Already exists"
                    self.stdout.write(
                        f"{action} ConnectingStation: {station.name} - {line.name}"
                    )

    def verify_data_integrity(self):
        """Verify data integrity after population"""
        verification_results = {
            "lines": Line.objects.count(),
            "stations": Station.objects.count(),
            "connections": ConnectingStation.objects.count(),
            "line_stations": LineStation.objects.count()
        }

        # Verify all stations have coordinates
        stations_without_coords = Station.objects.filter(
            Q(latitude__isnull=True) | Q(longitude__isnull=True)  # Use the imported Q
        ).count()

        if stations_without_coords > 0:
            self.stdout.write(
                self.style.WARNING(f"Found {stations_without_coords} stations without coordinates")
            )

        # Verify connecting stations
        for conn in self.CONNECTING_STATIONS:
            try:
                station = Station.objects.get(name=conn["name"])
                connected_lines = station.lines.count()
                if connected_lines != len(conn["lines"]):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Connection mismatch for {station.name}: "
                            f"Expected {len(conn['lines'])} lines, found {connected_lines}"
                        )
                    )
            except Station.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Connecting station not found: {conn['name']}")
                )

        # Print verification results
        self.stdout.write("\nVerification Results:")
        for key, value in verification_results.items():
            self.stdout.write(f"- {key}: {value}")

        return verification_results
