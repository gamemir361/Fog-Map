from types import SimpleNamespace
from app.modules.exploration.service import (
    apply_discovery_preferences,
    compute_recommendation_score,
    get_dominant_user_vibes,
)


def test_recommendation_cosine_score():
    user = SimpleNamespace(
        pref_nature=0.9,
        pref_history=0.1,
        pref_crowded=0.1,
        pref_quiet=0.8,
        pref_nightlife=0.1,
        pref_luxury=0.1,
        pref_budget=0.5,
        pref_romantic=0.2,
        pref_family=0.5,
        pref_study=0.6,
        pref_photography=0.9,
        pref_food=0.4,
    )
    matching_poi_detail = SimpleNamespace(
        nature=0.9,
        history=0.1,
        crowded=0.1,
        quiet=0.8,
        nightlife=0.1,
        luxury=0.1,
        budget=0.5,
        romantic=0.2,
        family=0.5,
        study=0.6,
        photography=0.9,
        food=0.4,
    )

    score = compute_recommendation_score(user, matching_poi_detail)
    # Identical vectors should have a high match percentage (~90-100%)
    assert score >= 80.0


def test_dominant_vibes_extraction():
    user = SimpleNamespace(
        pref_nature=0.9,
        pref_history=0.2,
        pref_crowded=0.1,
        pref_quiet=0.7,
        pref_nightlife=0.1,
        pref_luxury=0.1,
        pref_budget=0.3,
        pref_romantic=0.2,
        pref_family=0.4,
        pref_study=0.5,
        pref_photography=0.8,
        pref_food=0.4,
    )

    dominant = get_dominant_user_vibes(user, top_k=3)
    assert dominant == ["nature", "photography", "quiet"]


def test_learning_update_with_alpha():
    user = SimpleNamespace(
        pref_nature=0.5,
        pref_history=0.5,
        pref_crowded=0.5,
        pref_quiet=0.5,
        pref_nightlife=0.5,
        pref_luxury=0.5,
        pref_budget=0.5,
        pref_romantic=0.5,
        pref_family=0.5,
        pref_study=0.5,
        pref_photography=0.5,
        pref_food=0.5,
    )
    nature_poi_detail = SimpleNamespace(
        nature=1.0,
        history=0.0,
        crowded=0.0,
        quiet=0.8,
        nightlife=0.0,
        luxury=0.0,
        budget=0.5,
        romantic=0.3,
        family=0.5,
        study=0.5,
        photography=0.8,
        food=0.2,
    )

    apply_discovery_preferences(user, nature_poi_detail, alpha=0.2)

    # 0.5 * 0.8 + 1.0 * 0.2 = 0.6
    assert user.pref_nature == 0.6
    # 0.5 * 0.8 + 0.0 * 0.2 = 0.4
    assert user.pref_history == 0.4
