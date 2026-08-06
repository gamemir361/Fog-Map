"""
Central POI Discovery Configuration File
Defines default discovery state percentages, radius thresholds, and animation parameters.
"""

POI_DISCOVERY_CONFIG = {
    "DEFAULT_HIDDEN_PERCENT": 0.30,   # 30% of POIs assigned HIDDEN state for new users
    "DEFAULT_UNKNOWN_PERCENT": 0.70,  # 70% of POIs assigned UNKNOWN state for new users
    "DISCOVERY_RADIUS_METERS": 200.0, # Distance in meters to auto-discover POIs
    "REVEAL_ANIMATION_MS": 450,       # Duration of reveal/transition CSS animation in ms
}
