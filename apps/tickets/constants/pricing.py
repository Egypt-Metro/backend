from typing import Dict, Optional
from apps.tickets.constants.choices import TicketChoices


class TicketPricing:
    @classmethod
    def get_ticket_details(cls, ticket_type: str) -> Optional[Dict]:
        """Get all details for a ticket type"""
        return TicketChoices.TICKET_TYPES.get(ticket_type)

    @classmethod
    def calculate_upgrade_details(cls, stations_count: int) -> Optional[Dict]:
        """Calculate upgrade details based on stations count"""
        next_type, next_details = TicketChoices.get_next_ticket_type(stations_count)
        if not next_type:
            return None

        current_type = None
        for type_name, details in TicketChoices.TICKET_TYPES.items():
            if details['max_stations'] >= stations_count:
                current_type = type_name
                break

        if not current_type:
            return None

        current_details = TicketChoices.TICKET_TYPES[current_type]

        return {
            'next_ticket_type': next_type,
            'price_difference': next_details['price'] - current_details['price'],
            'new_max_stations': next_details['max_stations'],
            'new_color': next_details['color'],
            'current_stations': stations_count
        }


class SubscriptionPricing:
    # Monthly subscription prices
    MONTHLY = {
        1: 310,  # 1 Zone
        2: 365,  # 2 Zones
        4: 425,  # 3-4 Zones
        6: 600,  # 5-6 Zones
    }

    # Quarterly subscription prices
    QUARTERLY = {
        1: 835,   # 1 Zone
        2: 990,   # 2 Zones
        4: 1250,  # 3-4 Zones
        6: 1670,  # 5-6 Zones
    }

    # Annual subscription prices
    ANNUAL = {
        'LINES_1_2': 3175,     # Lines 1 & 2
        'ALL_LINES': 4000,     # All Lines
    }


# Zone definitions
ZONE_STATIONS = {
    1: ["Al Shohadaa", "Ataba", "Naguib", "Saad Zaghloul", "Urabi", "Naser", "Opera", "Sadat"],
    2: ["AlSayyeda Zeinab", "El-Malek El-Saleh", "Mar Girgis", "El-Zahraa", "Dar El-Salam"],
    3: ["Dokki", "Bohooth", "Cairo University", "Faisal", "Giza", "Omm el Misryeen", "Sakiat Mekki", "El Mounib"],
    4: ["Al Ahram", "Koleyet El Banat", "Cairo Stadium", "Fair Zone", "Abbassia", "Abdou Pasha", "El Geish", "Bab El Shaaria"],
    5: ["Saray El-Qobba", "Hammamat El-Qobba", "Kobri El-Qobba", "Manshiet El-Sadr", "El-Demerdash", "Ghamra"],
    6: ["Shobra El Kheima", "Koliet El-Zeraa", "Mezallat", "Khalafawy", "Sainte Teresa", "Road El-Farag", "Massara"],
    7: ["Hadayeq El-Maadi", "Maadi", "Thakanat El-Maadi", "Tora El-Balad", "Kozzika", "Tora El-Asmant"],
    8: ["New El-Marg", "El-Marg", "Ezbet El-Nakhl", "Ain Shams", "El-Matareyya", "Helmeyet El-Zaitoun", "Hadayeq El-Zaitoun"],
    9: ["El-Maasara", "Hadayeq Helwan", "Wadi Hof", "Helwan University", "Ain Helwan", "Helwan"],
    10: ["Haroun", "Heliopolis", "Alf Masken", "El-Shams Club"],
}

# Zone travel matrix
ZONE_MATRIX = {
    "1": {"1": 1, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 3, "8": 3, "9": 4, "10": 3},
    "2": {"1": 2, "2": 1, "3": 3, "4": 3, "5": 3, "6": 3, "7": 2, "8": 4, "9": 3, "10": 4},
    "3": {"1": 2, "2": 3, "3": 1, "4": 3, "5": 3, "6": 3, "7": 2, "8": 4, "9": 2, "10": 4},
    "4": {"1": 2, "2": 3, "3": 3, "4": 1, "5": 2, "6": 3, "7": 4, "8": 2, "9": 4, "10": 2},
    "5": {"1": 2, "2": 3, "3": 3, "4": 2, "5": 1, "6": 2, "7": 4, "8": 2, "9": 4, "10": 2},
    "6": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 4, "8": 3, "9": 5, "10": 3},
    "7": {"1": 3, "2": 2, "3": 2, "4": 4, "5": 4, "6": 4, "7": 1, "8": 5, "9": 2, "10": 5},
    "8": {"1": 3, "2": 4, "3": 4, "4": 2, "5": 2, "6": 3, "7": 5, "8": 1, "9": 5, "10": 2},
    "9": {"1": 4, "2": 3, "3": 2, "4": 4, "5": 4, "6": 5, "7": 2, "8": 5, "9": 1, "10": 5},
    "10": {"1": 3, "2": 4, "3": 4, "4": 2, "5": 2, "6": 3, "7": 5, "8": 2, "9": 5, "10": 1}
}
