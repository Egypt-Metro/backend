# apps/stations/management/commands/populate_metro_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stations.models import Line, Station, LineStation, ConnectingStation


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
            "stations": [
                {"name": "Adly Mansour", "latitude": 30.14694, "longitude": 31.42139},
                {"name": "El Haykestep", "latitude": 30.14389, "longitude": 31.40472},
                {
                    "name": "Omar Ibn El-Khattab",
                    "latitude": 30.14056,
                    "longitude": 31.39417,
                },
                {"name": "Qobaa", "latitude": 30.13472, "longitude": 31.38389},
                {"name": "Hesham Barakat", "latitude": 30.13111, "longitude": 31.37389},
                {"name": "El-Nozha", "latitude": 30.12833, "longitude": 31.36000},
                {"name": "Nadi El-Shams", "latitude": 30.12222, "longitude": 31.34389},
                {"name": "Alf Maskan", "latitude": 30.11806, "longitude": 31.33972},
                {
                    "name": "Heliopolis Square",
                    "latitude": 30.10806,
                    "longitude": 31.33722,
                },
                {"name": "Haroun", "latitude": 30.10000, "longitude": 31.33278},
                {"name": "Al-Ahram", "latitude": 30.09139, "longitude": 31.32639},
                {
                    "name": "Koleyet El-Banat",
                    "latitude": 30.08361,
                    "longitude": 31.32889,
                },
                {"name": "Stadium", "latitude": 30.07306, "longitude": 31.31750},
                {"name": "Fair Zone", "latitude": 30.07333, "longitude": 31.30111},
                {"name": "Abbassia", "latitude": 30.06972, "longitude": 31.28083},
                {"name": "Abdou Pasha", "latitude": 30.06472, "longitude": 31.27472},
                {"name": "El Geish", "latitude": 30.06222, "longitude": 31.26694},
                {"name": "Bab El Shaaria", "latitude": 30.05389, "longitude": 31.25611},
                {"name": "Attaba", "latitude": 30.05250, "longitude": 31.24722},
                {"name": "Nasser", "latitude": 30.05306, "longitude": 31.23611},
                {"name": "Maspero", "latitude": 30.05556, "longitude": 31.23222},
                {"name": "Safaa Hegazy", "latitude": 30.06250, "longitude": 31.22361},
                {"name": "Kit Kat", "latitude": 30.06667, "longitude": 31.21250},
                {"name": "Sudan Street", "latitude": 30.06972, "longitude": 31.20472},
                {"name": "Imbaba", "latitude": 30.07583, "longitude": 31.20750},
                {"name": "El-Bohy", "latitude": 30.08222, "longitude": 31.21056},
                {
                    "name": "Al-Qawmeya Al-Arabiya",
                    "latitude": 30.09333,
                    "longitude": 31.20889,
                },
                {"name": "Ring Road", "latitude": 30.09639, "longitude": 31.19972},
                {
                    "name": "Rod al-Farag Axis",
                    "latitude": 30.10194,
                    "longitude": 31.18417,
                },
                {"name": "El-Tawfikeya", "latitude": 30.06528, "longitude": 31.20250},
                {"name": "Wadi El-Nil", "latitude": 30.05833, "longitude": 31.20000},
                {
                    "name": "Gamaat El Dowal Al-Arabiya",
                    "latitude": 30.05083,
                    "longitude": 31.19972,
                },
                {
                    "name": "Bulaq El-Dakroor",
                    "latitude": 30.03611,
                    "longitude": 31.19639,
                },
                {
                    "name": "Cairo University",
                    "latitude": 30.02611,
                    "longitude": 31.20111,
                },
            ],
        },
    ]

    CONNECTING_STATIONS = [
        {"name": "Sadat", "lines": ["First Line", "Second Line"]},
        {"name": "Nasser", "lines": ["First Line", "Third Line"]},
        {"name": "Al-Shohadaa", "lines": ["First Line", "Second Line"]},
        {"name": "Attaba", "lines": ["Second Line", "Third Line"]},
    ]

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting metro data population..."))

        self.clear_existing_data()
        self.populate_lines_and_stations()
        self.populate_connecting_stations()

        self.stdout.write(
            self.style.SUCCESS("Metro data population completed successfully.")
        )

    def clear_existing_data(self):
        """Clear existing LineStation and ConnectingStation data."""
        self.stdout.write("Clearing existing data...")
        LineStation.objects.all().delete()
        ConnectingStation.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Existing data cleared."))

    def populate_lines_and_stations(self):
        """Populate the metro lines and stations."""
        self.stdout.write("Populating metro lines and stations...")
        for line_data in self.METRO_DATA:
            line, created = Line.objects.update_or_create(
                name=line_data["line"]["name"],
                defaults={"color_code": line_data["line"].get("color_code")},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} line: {line.name}")

            for order, station_data in enumerate(line_data["stations"], start=1):
                station, created = Station.objects.update_or_create(
                    name=station_data["name"],
                    defaults={
                        "latitude": station_data.get("latitude"),
                        "longitude": station_data.get("longitude"),
                    },
                )
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} station: {station.name}")

                line_station, ls_created = LineStation.objects.update_or_create(
                    line=line, station=station, defaults={"order": order}
                )
                action = "Created" if ls_created else "Updated"
                self.stdout.write(
                    f"{action} LineStation: {line.name} - {station.name} (Order: {order})"
                )

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
