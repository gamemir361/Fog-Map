import pytest
from app.core.config.xp_config import XP_REWARDS
from app.modules.gamification.xp_engine import XPEngine


def test_xp_progression_level_calculation():
    # Level 1: 0 XP
    p0 = XPEngine.calculate_progression(0)
    assert p0["level"] == 1
    assert p0["xp_in_level"] == 0
    assert p0["xp_needed_for_next"] == 50
    assert p0["progress_pct"] == 0.0

    # 49 XP -> still Level 1 (98% progress)
    p49 = XPEngine.calculate_progression(49)
    assert p49["level"] == 1
    assert p49["xp_in_level"] == 49
    assert p49["progress_pct"] == 98.0

    # 50 XP -> Level 2
    p50 = XPEngine.calculate_progression(50)
    assert p50["level"] == 2
    assert p50["xp_in_level"] == 0
    assert p50["xp_needed_for_next"] == 150  # (2^2*50 - 1^2*50 = 200 - 50 = 150)
    assert p50["progress_pct"] == 0.0

    # 200 XP -> Level 3
    p200 = XPEngine.calculate_progression(200)
    assert p200["level"] == 3
    assert p200["xp_in_level"] == 0


def test_central_xp_rewards_config():
    assert XP_REWARDS["DISCOVER_AREA"] == 10
    assert XP_REWARDS["DISCOVER_POI"] == 25
    assert XP_REWARDS["VISIT_POI"] == 15
    assert XP_REWARDS["COMPLETE_ROUTE"] == 50
    assert XP_REWARDS["MILESTONE_10_AREAS"] == 50
