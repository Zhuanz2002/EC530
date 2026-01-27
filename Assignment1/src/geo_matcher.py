"""
geo_matcher.py

A utility module for matching geographic locations.

This module provides functions to compute the great-circle distance
between two GPS coordinates and to find the closest location from
a list of candidate locations.

All locations are assumed to be provided as:
    (latitude, longitude) in decimal degrees.
"""

import math
from typing import List, Tuple

# Type alias for readability
GeoLocation = Tuple[float, float]


def haversine_distance(loc1: GeoLocation, loc2: GeoLocation) -> float:
    """
    Compute the great-circle distance between two GPS locations
    using the Haversine formula.

    Parameters
    ----------
    loc1 : (float, float)
        (latitude, longitude) of the first location in decimal degrees
    loc2 : (float, float)
        (latitude, longitude) of the second location in decimal degrees

    Returns
    -------
    float
        Distance between the two locations in kilometers
    """
    # Earth radius in kilometers
    earth_radius_km = 6371.0

    lat1, lon1 = loc1
    lat2, lon2 = loc2

    # Convert degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius_km * c


def find_closest_location(
    current_location: GeoLocation,
    candidate_locations: List[GeoLocation],
) -> GeoLocation:
    """
    Find the closest geographic location to the current location.

    Parameters
    ----------
    current_location : (float, float)
        The reference GPS location (latitude, longitude)
    candidate_locations : list of (float, float)
        A list of GPS locations to compare against

    Returns
    -------
    (float, float)
        The closest GPS location from candidate_locations

    Raises
    ------
    ValueError
        If candidate_locations is empty
    """
    if not candidate_locations:
        raise ValueError("candidate_locations must not be empty")

    closest_location = candidate_locations[0]
    min_distance = haversine_distance(current_location, closest_location)

    for location in candidate_locations[1:]:
        distance = haversine_distance(current_location, location)
        if distance < min_distance:
            min_distance = distance
            closest_location = location

    return closest_location
