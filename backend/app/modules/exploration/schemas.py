from typing import Any, Optional
from pydantic import BaseModel


class POIResponse(BaseModel):
    id: int
    name: str
    category: str
    lat: float
    lon: float
    description: str = ""
    vectors: dict[str, float] = {}
    match_percentage: Optional[float] = None
    is_discovered: bool = False
    discovery_state: str = "unknown"
    discovered_at: Optional[str] = None
    discovery_source: Optional[str] = None
    rarity: str = "common"
    poi_type: str = "standard"
    is_secret: bool = False
    expires_at: Optional[str] = None
    xp_reward: Optional[int] = 25

    class Config:
        from_attributes = True


class FogDiscoverRequest(BaseModel):
    user_id: int = 1
    lat: float
    lon: float


class FogDiscoverResponse(BaseModel):
    status: Optional[str] = "success"
    message: str
    current_points: int
    all_points: list[dict[str, float]]
    user_preferences: Optional[dict[str, float]] = None
    progression: Optional[dict[str, Any]] = None
    xp_feedback: Optional[dict[str, Any]] = None


class RoutePlanRequest(BaseModel):
    lat: float
    lon: float
    mood: str


class RoutePlanResponse(BaseModel):
    status: str
    message: str
    route_coordinates: list[list[float]]


class ExplorationEventResponse(BaseModel):
    id: int
    title: str
    description: str
    event_type: str
    status: str
    latitude: float
    longitude: float
    radius_meters: float
    distance_meters: float
    inside_geofence: bool
    already_participated: bool = False
    xp_reward: int
    starts_at: str
    ends_at: str
    is_active: bool = True
    remaining_seconds: Optional[int] = None
    formatted_remaining_time: Optional[str] = None
    is_ending_soon: bool = False

    class Config:
        from_attributes = True


class NearbyEventsResponse(BaseModel):
    status: str = "success"
    message: str
    count: int
    events: list[ExplorationEventResponse]


class SingleEventResponse(BaseModel):
    status: str = "success"
    event: ExplorationEventResponse


class EventParticipateRequest(BaseModel):
    latitude: float
    longitude: float


class EventParticipateResponse(BaseModel):
    status: str
    message: str
    event_id: int
    event_title: str
    distance_meters: float
    xp_earned: int
    already_participated: bool
    progression: Optional[dict[str, Any]] = None


class EventClusterItem(BaseModel):
    latitude: float
    longitude: float
    event_count: int
    event_types: dict[str, int]


class EventDensityResponse(BaseModel):
    status: str = "success"
    zoom: int
    count: int
    clusters: list[EventClusterItem]


class EventLeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    display_name: str
    score: int


class CurrentUserEventRank(BaseModel):
    has_participated: bool
    rank: Optional[int] = None
    score: Optional[int] = None
    user_id: int


class CommunityChallengeProgress(BaseModel):
    enabled: bool = True
    status: str  # "upcoming", "active", "completed", "expired"
    target_participants: int
    current_participants: int
    participants_progress_pct: float
    target_xp: int
    current_xp: int
    xp_progress_pct: float
    community_reward_xp: int


class EventLeaderboardResponse(BaseModel):
    status: str = "success"
    event_id: int
    event_title: str
    participant_count: int
    total_xp_earned: int
    entries: list[EventLeaderboardEntry]
    current_user: Optional[CurrentUserEventRank] = None
    challenge: CommunityChallengeProgress


class EventActivityItem(BaseModel):
    id: int
    event_id: int
    event_title: str
    user_id: Optional[int] = None
    display_name: Optional[str] = None
    activity_type: str  # "participation", "challenge_progress", "challenge_completed"
    title: str
    description: str
    xp_earned: int = 0
    progress_pct: Optional[float] = None
    created_at: str


class EventActivityFeedResponse(BaseModel):
    status: str = "success"
    count: int
    activities: list[EventActivityItem]