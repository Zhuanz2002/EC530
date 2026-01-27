"""
Unit tests for geo_matcher.py

Run from Assignment1/ directory:
    pytest -q
"""

import math
import pytest

# Import the functions under test
# If your repo structure differs, adjust this import accordingly.
from src.geo_matcher import haversine_distance, find_closest_location


def test_haversine_distance_zero_for_same_point():
    """Distance from a point to itself should be ~0."""
    loc = (42.3601, -71.0589)
    assert haversine_distance(loc, loc) == pytest.approx(0.0, abs=1e-9)


def test_haversine_distance_is_symmetric():
    """Distance should be symmetric: d(a,b) == d(b,a)."""
    a = (42.3601, -71.0589)  # Boston-ish
    b = (40.7128, -74.0060)  # NYC-ish
    assert haversine_distance(a, b) == pytest.approx(haversine_distance(b, a), rel=1e-12)


def test_haversine_distance_reasonable_value_boston_to_nyc():
    """
    Sanity check against a known ballpark distance.

    Boston <-> NYC great-circle distance is roughly ~300 km.
    We allow a wide tolerance since we're only sanity-checking.
    """
    boston = (42.3601, -71.0589)
    nyc = (40.7128, -74.0060)
    d_km = haversine_distance(boston, nyc)
    assert 250.0 <= d_km <= 400.0


def test_find_closest_location_returns_exact_match_if_present():
    """If the current location exists in candidates, it should be the closest."""
    current = (1.0, 2.0)
    candidates = [(10.0, 10.0), current, (3.0, 4.0)]
    assert find_closest_location(current, candidates) == current


def test_find_closest_location_picks_nearest():
    """Choose the candidate with the smallest great-circle distance."""
    current = (0.0, 0.0)

    # Near vs far on the globe (approx comparisons are fine)
    near = (0.0, 0.1)
    far = (10.0, 10.0)

    candidates = [far, near]
    assert find_closest_location(current, candidates) == near


def test_find_closest_location_raises_on_empty_candidates():
    """Empty candidate list should raise a clear error."""
    with pytest.raises(ValueError):
        find_closest_location((0.0, 0.0), [])
