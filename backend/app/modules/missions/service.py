import json
import math
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.exploration.models import DiscoveredArea, POI, UserPOIState
from app.modules.exploration.repository import ExplorationRepository
from app.modules.gamification.models import XPLog
from app.modules.gamification.xp_engine import XPEngine
from app.modules.missions.models import Mission
from app.modules.missions.repository import MissionsRepository


def calculate_user_level(score: int):
    prog = XPEngine.calculate_progression(score)
    return {
        "level": prog["level"],
        "score": prog["total_xp"],
        "xp_in_level": prog["xp_in_level"],
        "xp_needed_for_next": prog["xp_needed_for_next"],
        "progress_pct": prog["progress_pct"],
    }


def seed_missions(db: Session):
    repo = MissionsRepository(db)
    if repo.get_mission_count() == 0:
        repo.create_missions_bulk(
            [
                Mission(
                    title="اولین قدم‌ها",
                    description="۱۰ منطقه جدید را در کلان‌شهر کشف کنید",
                    event_type="discover_area",
                    target=10,
                    reward_points=50,
                    badge_name="پایونیر کلان‌شهر",
                    badge_icon="🧭",
                ),
                Mission(
                    title="کاشف شهر",
                    description="۵۰ منطقه از نقشه شهر را از مه خارج کنید",
                    event_type="discover_area",
                    target=50,
                    reward_points=150,
                    badge_name="کاشف برجسته",
                    badge_icon="🗺️",
                ),
                Mission(
                    title="شهر زیر پاهای من",
                    description="۱۰۰ منطقه شهری را فتح کنید",
                    event_type="discover_area",
                    target=100,
                    reward_points=300,
                    badge_name="سلطان کاوش",
                    badge_icon="👑",
                ),
                Mission(
                    title="نخستین کشف مکان",
                    description="اولین مکان شاخص را در شهر پیدا و کشف کنید",
                    event_type="visit_poi",
                    target=1,
                    reward_points=25,
                    badge_name="جویاگر",
                    badge_icon="📍",
                ),
                Mission(
                    title="مجموعه‌دار اماکن",
                    description="۵ مکان شاخص شهری را کشف و ثبت کنید",
                    event_type="visit_poi",
                    target=5,
                    reward_points=75,
                    badge_name="مجموعه‌دار مکان",
                    badge_icon="🏛️",
                ),
                Mission(
                    title="استاد کاوشگری",
                    description="۱۰ مکان شاخص کلان‌شهر را کشف کنید",
                    event_type="visit_poi",
                    target=10,
                    reward_points=150,
                    badge_name="استاد کاوش",
                    badge_icon="⭐",
                ),
                Mission(
                    title="کاوشگر فرهنگ و تاریخ",
                    description="یک مکان دارای اتمسفر فرهنگی یا تاریخی را کشف کنید",
                    event_type="visit_poi",
                    conditions_json=json.dumps({"category": "culture"}),
                    target=1,
                    reward_points=30,
                    badge_name="کاوشگر فرهنگ",
                    badge_icon="📜",
                ),
                Mission(
                    title="دوست‌دار طبیعت",
                    description="از یک بوستان یا مکان طبیعی و سرسبز بازدید کنید",
                    event_type="visit_poi",
                    conditions_json=json.dumps({"category": "nature"}),
                    target=1,
                    reward_points=30,
                    badge_name="دوست‌دار طبیعت",
                    badge_icon="🌿",
                ),
            ]
        )


def list_active_missions(db: Session):
    repo = MissionsRepository(db)
    return repo.get_active_missions()


def update_user_missions(db: Session, user_id: int, action_type: str, context: dict = None):
    missions_repo = MissionsRepository(db)
    active_missions = missions_repo.get_active_missions()

    for mission in active_missions:
        if mission.event_type and mission.event_type != action_type:
            continue

        user_mission = missions_repo.get_user_mission(user_id, mission.id)
        if not user_mission:
            user_mission = missions_repo.create_user_mission(user_id, mission.id, progress=0)

        if user_mission.is_completed:
            continue

        should_update = False

        if action_type == "discover_area":
            disc_count = db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).count()
            user_mission.progress = disc_count
            should_update = True

        elif action_type == "visit_poi":
            if mission.conditions_json:
                try:
                    conds = json.loads(mission.conditions_json)
                    req_cat = conds.get("category")
                    if req_cat:
                        cat_count = (
                            db.query(UserPOIState)
                            .join(POI, UserPOIState.poi_id == POI.id)
                            .filter(
                                UserPOIState.user_id == user_id,
                                UserPOIState.state == "discovered",
                                POI.category == req_cat,
                            )
                            .count()
                        )
                        user_mission.progress = cat_count
                        should_update = True
                except Exception:
                    pass
            else:
                total_pois = (
                    db.query(UserPOIState)
                    .filter(UserPOIState.user_id == user_id, UserPOIState.state == "discovered")
                    .count()
                )
                user_mission.progress = total_pois
                should_update = True

        if should_update and user_mission.progress >= mission.target:
            user_mission.is_completed = True
            user_mission.completed_at = datetime.utcnow()

            XPEngine.award_xp(
                db,
                user_id,
                "MISSION_COMPLETE",
                entity_id=f"mission_{mission.id}",
                reason=f"تکمیل دستاورد '{mission.title}'",
                custom_xp=mission.reward_points,
            )

            if mission.badge_name:
                missions_repo.grant_badge(
                    user_id, mission.badge_name, mission.badge_icon or "⭐"
                )

    db.commit()


def get_user_gamification_profile(db: Session, user_id: int = 1):
    missions_repo = MissionsRepository(db)
    exploration_repo = ExplorationRepository(db)

    user = exploration_repo.get_user_by_id(user_id)
    score = user.score if user else 0

    level_stats = calculate_user_level(score)
    badges = missions_repo.get_user_badges(user_id)
    user_missions = missions_repo.get_all_user_missions(user_id)

    # 1. Calculate Real Exploration Stats
    discovered_areas_cnt = db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).count()
    discovered_pois_cnt = db.query(UserPOIState).filter(UserPOIState.user_id == user_id, UserPOIState.state == "discovered").count()

    cat_rows = (
        db.query(POI.category)
        .join(UserPOIState, UserPOIState.poi_id == POI.id)
        .filter(UserPOIState.user_id == user_id, UserPOIState.state == "discovered")
        .distinct()
        .all()
    )
    categories_cnt = len(cat_rows)

    first_area = (
        db.query(DiscoveredArea)
        .filter(DiscoveredArea.user_id == user_id)
        .order_by(DiscoveredArea.discovered_at.asc())
        .first()
    )
    first_discovery_date = first_area.discovered_at.isoformat() if first_area and first_area.discovered_at else None

    recent_log = (
        db.query(XPLog)
        .filter(XPLog.user_id == user_id)
        .order_by(XPLog.timestamp.desc())
        .first()
    )
    recent_activity_date = recent_log.timestamp.isoformat() if recent_log and recent_log.timestamp else None

    explored_area_sqkm = round(discovered_areas_cnt * 0.0707, 2)

    stats = {
        "total_xp": score,
        "level": level_stats["level"],
        "discovered_areas_count": discovered_areas_cnt,
        "discovered_pois_count": discovered_pois_cnt,
        "explored_area_sqkm": explored_area_sqkm,
        "discovered_categories_count": categories_cnt,
        "first_discovery_date": first_discovery_date,
        "recent_activity_date": recent_activity_date,
    }

    # 2. Milestones List
    mission_progress_list = []
    active_missions = missions_repo.get_active_missions()
    user_m_map = {um.mission_id: um for um in user_missions}

    for m in active_missions:
        um = user_m_map.get(m.id)
        prog = um.progress if um else 0
        is_comp = um.is_completed if um else False
        comp_at = um.completed_at.isoformat() if (um and um.completed_at) else None
        mission_progress_list.append(
            {
                "id": m.id,
                "title": m.title,
                "description": m.description,
                "target": m.target,
                "reward_points": m.reward_points,
                "badge_name": m.badge_name,
                "badge_icon": m.badge_icon,
                "progress": prog,
                "is_completed": is_comp,
                "completed_at": comp_at,
            }
        )

    # 3. Real Recent Activity Feed from XPLog
    xp_logs = (
        db.query(XPLog)
        .filter(XPLog.user_id == user_id)
        .order_by(XPLog.timestamp.desc())
        .limit(15)
        .all()
    )

    activity_feed = []
    for log in xp_logs:
        icon = "📍"
        if log.event_type == "DISCOVER_AREA":
            icon = "🗺️"
        elif log.event_type == "DISCOVER_POI":
            icon = "🏛️"
        elif log.event_type == "MISSION_COMPLETE":
            icon = "🏆"
        elif log.event_type == "COMPLETE_ROUTE":
            icon = "🧭"

        activity_feed.append(
            {
                "id": log.id,
                "event_type": log.event_type,
                "title": log.reason or "فعالیت کاوش",
                "xp_value": log.xp_value,
                "icon": icon,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
        )

    return {
        "user_id": user_id,
        "score": score,
        "level_stats": level_stats,
        "stats": stats,
        "badges": [
            {
                "name": b.badge_name,
                "icon": b.badge_icon,
                "unlocked_at": b.unlocked_at.isoformat() if b.unlocked_at else None,
            }
            for b in badges
        ],
        "missions": mission_progress_list,
        "milestones": mission_progress_list,
        "recent_activities": activity_feed,
    }
