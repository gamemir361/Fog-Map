from app.modules.missions.service import calculate_user_level


def test_calculate_user_level_math():
    # Score 0 => Level 1
    stats0 = calculate_user_level(0)
    assert stats0["level"] == 1
    assert stats0["xp_in_level"] == 0
    assert stats0["xp_needed_for_next"] == 50

    # Score 50 => Level 2
    stats50 = calculate_user_level(50)
    assert stats50["level"] == 2

    # Score 200 => Level 3 (level = floor(sqrt(200/50))+1 = floor(2)+1 = 3)
    stats200 = calculate_user_level(200)
    assert stats200["level"] == 3
