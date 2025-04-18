class TicketPricing:
    # Ticket pricing based on number of stations
    STATION_PRICES = {
        9: 8,    # Up to 9 stations: 8 EGP
        16: 10,  # Up to 16 stations: 10 EGP
        23: 15,  # Up to 23 stations: 15 EGP
        39: 20,  # Up to 39 stations: 20 EGP
    }


class SubscriptionPricing:
    # Monthly subscription prices
    MONTHLY = {
        1: 310,  # 1 Zone
        2: 365,  # 2 Zones
        3: 425,  # 3-4 Zones
        4: 600,  # 5-6 Zones
    }

    # Quarterly subscription prices
    QUARTERLY = {
        1: 835,   # 1 Zone
        2: 990,   # 2 Zones
        3: 1250,  # 3-4 Zones
        4: 1670,  # 5-6 Zones
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
