from types import SimpleNamespace

from app.modules.exploration.service import (
    apply_discovery_preferences,
    build_discovery_message,
    build_poi_payload,
    compute_recommendation_score,
)


def test_build_poi_payload_serializes_coordinates_and_vectors():
    poi = SimpleNamespace(
        id=7,
        name="Ghalamestan",
        category="culture",
        geometry=SimpleNamespace(x=51.4, y=35.7),
        details=SimpleNamespace(
            description="A cultural place",
            nature=0.8,
            history=0.9,
            crowded=0.1,
            quiet=0.7,
            nightlife=0.2,
            luxury=0.3,
            budget=0.6,
            romantic=0.4,
            family=0.5,
            study=0.6,
            photography=0.7,
            food=0.5,
        ),
    )

    payload = build_poi_payload(poi)

    assert payload["id"] == 7
    assert payload["name"] == "Ghalamestan"
    assert payload["lat"] == 35.7
    assert payload["lon"] == 51.4
    assert payload["vectors"]["nature"] == 0.8
    assert payload["description"] == "A cultural place"


def test_compute_recommendation_score_prefers_matching_user_tastes():
    user = SimpleNamespace(pref_nature=0.9, pref_history=0.2, pref_crowded=0.1, pref_quiet=0.8, pref_nightlife=0.2, pref_luxury=0.3, pref_budget=0.4, pref_romantic=0.2, pref_family=0.6, pref_study=0.7, pref_photography=0.8, pref_food=0.3)
    detail = SimpleNamespace(nature=0.9, history=0.2, crowded=0.2, quiet=0.8, nightlife=0.1, luxury=0.1, budget=0.5, romantic=0.2, family=0.6, study=0.7, photography=0.8, food=0.4)

    score = compute_recommendation_score(user, detail)

    assert score > 1.0


def test_apply_discovery_preferences_updates_user_tastes():
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
    detail = SimpleNamespace(
        nature=0.8,
        history=0.2,
        crowded=0.4,
        quiet=0.7,
        nightlife=0.3,
        luxury=0.1,
        budget=0.6,
        romantic=0.5,
        family=0.9,
        study=0.4,
        photography=0.2,
        food=0.7,
    )

    apply_discovery_preferences(user, detail, alpha=0.2)

    assert user.pref_nature > 0.5
    assert user.pref_family > 0.5
    assert user.pref_food > 0.5


def test_build_discovery_message_includes_vibe_context():
    message = build_discovery_message(10, "Meydan-e-Shah")

    assert "10 XP" in message
    assert "Meydan-e-Shah" in message
