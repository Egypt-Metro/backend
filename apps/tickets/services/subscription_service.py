# apps/tickets/services/subscription_service.py
import logging
from datetime import timedelta
from django.db import DatabaseError, ProgrammingError, transaction
from django.utils import timezone

from apps.stations.models import Station
from ..models.subscription import SubscriptionPlan, UserSubscription, StationZone, ZoneMatrix
from ..constants.pricing import SubscriptionPricing, ZONE_STATIONS, ZONE_MATRIX

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self):
        try:
            self._ensure_zone_data()
        except (DatabaseError, ProgrammingError):
            logger.warning("Database tables not ready yet. Zone matrix initialization skipped.")

    def _ensure_zone_data(self):
        """Ensure zone data is initialized in the database"""
        try:
            if not ZoneMatrix.objects.exists():
                self._initialize_zone_matrix()
        except (DatabaseError, ProgrammingError) as e:
            logger.warning(f"Could not check zone matrix: {str(e)}")
            raise  # Re-raise the exception to be caught by __init__

    def _initialize_zone_matrix(self):
        """Initialize the zone matrix in the database"""
        matrix_entries = []
        for source_zone, destinations in ZONE_MATRIX.items():
            for dest_zone, zones_crossed in destinations.items():
                matrix_entries.append(ZoneMatrix(
                    source_zone=int(source_zone),
                    destination_zone=int(dest_zone),
                    zones_crossed=zones_crossed
                ))
        ZoneMatrix.objects.bulk_create(matrix_entries)
        logger.info(f"Initialized {len(matrix_entries)} zone matrix entries")

    def get_station_zone(self, station_id):
        """Get zone number for a station"""
        try:
            station_zone = StationZone.objects.filter(station_id=station_id).first()
            if station_zone:
                return station_zone.zone_number

            # If not found in database, try to find in constants
            station = Station.objects.get(id=station_id)
            for zone_num, stations in ZONE_STATIONS.items():
                if any(station_name.lower() in station.name.lower() for station_name in stations):
                    # Create the mapping in the database for future lookups
                    StationZone.objects.create(station=station, zone_number=zone_num)
                    return zone_num

            return None
        except Exception as e:
            logger.error(f"Error getting station zone: {str(e)}")
            return None

    def get_zones_between(self, start_station_id, end_station_id):
        """Calculate zones between two stations"""
        start_zone = self.get_station_zone(start_station_id)
        end_zone = self.get_station_zone(end_station_id)

        if not start_zone or not end_zone:
            return None

        try:
            # First check database
            matrix_entry = ZoneMatrix.objects.filter(
                source_zone=start_zone,
                destination_zone=end_zone
            ).first()

            if matrix_entry:
                return matrix_entry.zones_crossed

            # If not in database, use the constants
            return ZONE_MATRIX[str(start_zone)][str(end_zone)]
        except Exception as e:
            logger.error(f"Error calculating zones between stations: {str(e)}")
            return None

    def get_price_category(self, num_zones):
        """Get price category based on number of zones"""
        if num_zones == 1:
            return 1
        elif num_zones == 2:
            return 2
        elif num_zones in [3, 4]:
            return 4
        elif num_zones in [5, 6]:
            return 6
        return None

    def get_station_lines(self, station_id):
        """Get metro lines for a station"""
        try:
            station = Station.objects.get(id=station_id)
            return [line.name for line in station.lines.all()]
        except Exception as e:
            logger.error(f"Error getting station lines: {str(e)}")
            return []

    def recommend_subscription(self, start_station_id, end_station_id):
        """Generate subscription recommendations based on journey"""
        try:
            # Get stations
            start_station = Station.objects.get(id=start_station_id)
            end_station = Station.objects.get(id=end_station_id)

            # Calculate zones
            num_zones = self.get_zones_between(start_station_id, end_station_id)

            if num_zones is None:
                return {"error": "Could not determine zones between stations"}

            # Get price category for monthly/quarterly plans
            price_category = self.get_price_category(num_zones)

            # Get lines for annual plan recommendation
            start_lines = self.get_station_lines(start_station_id)
            end_lines = self.get_station_lines(end_station_id)

            # Check if journey only requires lines 1 and 2
            all_lines = set(start_lines + end_lines)
            only_lines_1_2 = all(line in ["First Line", "Second Line"] for line in all_lines)

            # Prepare recommendations
            recommendations = {
                "start_station": start_station.name,
                "end_station": end_station.name,
                "zones_traveled": num_zones,
                "recommendations": []
            }

            # Monthly recommendation
            monthly_price = SubscriptionPricing.MONTHLY.get(price_category)
            if monthly_price:
                recommendations["recommendations"].append({
                    "plan_type": "Monthly",
                    "price": monthly_price,
                    "zones": num_zones,
                    "price_per_trip": round(monthly_price / 60, 2),  # Assuming 2 trips per day, 30 days
                    "description": f"Monthly subscription for {num_zones} zones"
                })

            # Quarterly recommendation
            quarterly_price = SubscriptionPricing.QUARTERLY.get(price_category)
            if quarterly_price:
                recommendations["recommendations"].append({
                    "plan_type": "Quarterly",
                    "price": quarterly_price,
                    "zones": num_zones,
                    "price_per_trip": round(quarterly_price / 180, 2),  # Assuming 2 trips per day, 90 days
                    "description": f"Quarterly subscription for {num_zones} zones"
                })

            # Annual recommendation
            if only_lines_1_2:
                annual_price = SubscriptionPricing.ANNUAL['LINES_1_2']
                lines_text = "Lines 1 & 2"
            else:
                annual_price = SubscriptionPricing.ANNUAL['ALL_LINES']
                lines_text = "All Lines (1, 2, 3)"

            recommendations["recommendations"].append({
                "plan_type": "Annual",
                "price": annual_price,
                "lines": lines_text,
                "price_per_trip": round(annual_price / 730, 2),  # Assuming 2 trips per day, 365 days
                "description": f"Annual subscription for {lines_text}"
            })

            # Sort recommendations by price per trip (most economical first)
            recommendations["recommendations"] = sorted(
                recommendations["recommendations"],
                key=lambda x: x["price_per_trip"]
            )

            return recommendations

        except Station.DoesNotExist:
            return {"error": "One or both stations do not exist"}
        except Exception as e:
            logger.error(f"Error recommending subscription: {str(e)}")
            return {"error": str(e)}

    @transaction.atomic
    def create_subscription(self, user, subscription_type, zones_count, payment_confirmed=False, start_station_id=None, end_station_id=None):
        """Creates a new subscription"""
        if not payment_confirmed:
            raise ValueError("Payment must be confirmed")

        try:
            # Calculate price based on subscription type and zones
            if subscription_type == 'ANNUAL':
                lines = ['First Line', 'Second Line'] if zones_count == 2 else ['First Line', 'Second Line', 'Third Line']
                price = SubscriptionPricing.ANNUAL['LINES_1_2'] if zones_count == 2 else SubscriptionPricing.ANNUAL['ALL_LINES']

                # Create or get subscription plan
                plan_name = 'Annual Lines 1&2' if zones_count == 2 else 'Annual All Lines'
                plan, _ = SubscriptionPlan.objects.get_or_create(
                    type=subscription_type,
                    lines=lines,
                    defaults={
                        'name': plan_name,
                        'price': price,
                        'description': f'Annual subscription for {", ".join(lines)}'
                    }
                )
            else:
                # For MONTHLY and QUARTERLY
                if subscription_type == 'MONTHLY':
                    price_mapping = SubscriptionPricing.MONTHLY
                else:  # QUARTERLY
                    price_mapping = SubscriptionPricing.QUARTERLY

                # Determine price category
                price_category = self.get_price_category(zones_count)
                if not price_category:
                    raise ValueError(f"Invalid zones count: {zones_count}")

                price = price_mapping.get(price_category)

                # Create or get subscription plan
                plan_name = f"{subscription_type.capitalize()} {zones_count} Zone{'s' if zones_count > 1 else ''}"
                plan, _ = SubscriptionPlan.objects.get_or_create(
                    type=subscription_type,
                    zones=zones_count,
                    defaults={
                        'name': plan_name,
                        'price': price,
                        'description': f"{subscription_type.capitalize()} subscription for {zones_count} zone{'s' if zones_count > 1 else ''}"
                    }
                )

            # Calculate dates
            start_date = timezone.now().date()
            if subscription_type == 'MONTHLY':
                end_date = start_date + timedelta(days=30)
            elif subscription_type == 'QUARTERLY':
                end_date = start_date + timedelta(days=90)
            else:  # ANNUAL
                end_date = start_date + timedelta(days=365)

            # Get optional stations
            start_station = Station.objects.get(id=start_station_id) if start_station_id else None
            end_station = Station.objects.get(id=end_station_id) if end_station_id else None

            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                status='ACTIVE',
                start_station=start_station,
                end_station=end_station
            )

            return subscription

        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise ValueError(f"Failed to create subscription: {str(e)}")

    def validate_subscription(self, user, station_name):
        """Validates if a user's subscription covers a given station"""
        active_sub = UserSubscription.objects.filter(
            user=user,
            status='ACTIVE',
            end_date__gte=timezone.now().date()
        ).first()

        if not active_sub:
            return {
                'valid': False,
                'message': 'No active subscription'
            }

        # Find zone for the station
        station_zone = None
        for zone_num, stations in ZONE_STATIONS.items():
            if station_name in stations:
                station_zone = zone_num
                break

        if not station_zone:
            return {
                'valid': False,
                'message': 'Invalid station'
            }

        # Check if zone is covered by subscription
        if active_sub.plan.type == 'ANNUAL':
            # For annual plans, check based on lines
            lines = active_sub.plan.lines or []
            if any('Third Line' in line for line in lines):
                # All lines covers all zones
                return {
                    'valid': True,
                    'message': 'Valid subscription for all lines'
                }
            elif station_zone <= 9:  # Lines 1&2 cover zones 1-9
                return {
                    'valid': True,
                    'message': 'Valid subscription for Lines 1 & 2'
                }
        else:
            # For monthly/quarterly, check if zone is covered based on plan zones
            if active_sub.plan.zones and station_zone <= active_sub.plan.zones:
                return {
                    'valid': True,
                    'message': f'Valid {active_sub.plan.type} subscription'
                }

        return {
            'valid': False,
            'message': 'Station not covered by subscription'
        }
