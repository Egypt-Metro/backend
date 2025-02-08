# apps/routes/services/cache_service.py

from django.core.cache import cache


class CacheService:
    """
    A service class for caching metro routes to improve performance.
    """

    @staticmethod
    def get_cached_route(start_station_id, end_station_id):
        """
        Retrieves a cached route if available.

        :param start_station_id: ID of the starting station.
        :param end_station_id: ID of the destination station.
        :return: Cached route data if available, otherwise None.
        """
        cache_key = CacheService._generate_cache_key(start_station_id, end_station_id)
        return cache.get(cache_key)

    @staticmethod
    def cache_route(start_station_id, end_station_id, route_data, timeout=3600):
        """
        Caches the computed route for future use.

        :param start_station_id: ID of the starting station.
        :param end_station_id: ID of the destination station.
        :param route_data: The route data to cache.
        :param timeout: Cache timeout in seconds (default: 1 hour).
        """
        cache_key = CacheService._generate_cache_key(start_station_id, end_station_id)
        cache.set(cache_key, route_data, timeout)

    @staticmethod
    def delete_cached_route(start_station_id, end_station_id):
        """
        Deletes a cached route if it exists.

        :param start_station_id: ID of the starting station.
        :param end_station_id: ID of the destination station.
        """
        cache_key = CacheService._generate_cache_key(start_station_id, end_station_id)
        cache.delete(cache_key)

    @staticmethod
    def clear_routes_for_stations(*stations):
        """
        Clears only the affected routes related to the provided stations.

        :param stations: List of station objects that may be affected.
        """
        if not stations:
            return

        station_ids = [station.id for station in stations]

        # Generate cache keys for all possible route combinations involving the affected stations
        cache_keys = []
        for start_station in station_ids:
            for end_station in station_ids:
                if start_station != end_station:
                    cache_keys.append(CacheService._generate_cache_key(start_station, end_station))

        # Bulk delete cache entries
        cache.delete_many(cache_keys)

    @staticmethod
    def clear_all_routes():
        """
        Clears all cached routes.
        """
        cache.clear()

    @staticmethod
    def _generate_cache_key(start_station_id, end_station_id):
        """
        Generates a standardized cache key for a given route.

        :param start_station_id: ID of the starting station.
        :param end_station_id: ID of the destination station.
        :return: A formatted cache key string.
        """
        return f"route:{start_station_id}-{end_station_id}"
