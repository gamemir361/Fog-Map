import json
import math
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.exploration.repository import ExplorationRepository
from app.modules.missions.models import Mission
from app.modules.missions.repository import MissionsRepository


from app.modules.gamification.xp_engine import XPEngine


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
                    title="کشف 3 منطقه",
                    description="سه منطقه جدید را در نقشه کلان‌شهر کشف کنید",
                    event_type="discover_area",
                    target=3,
                    reward_points=30,
                    badge_name="پایونیر کلان‌شهر",
                    badge_icon="🧭",
                ),
                Mission(
                    title="پیدا کردن یک نقطه فرهنگی",
                    description="یک POI دارای اتمسفر فرهنگی یا تاریخی را کشف کنید",
                    event_type="visit_poi",
                    conditions_json=json.dumps({"category": "culture"}),
                    target=1,
                    reward_points=20,
                    badge_name="کاوشگر فرهنگ",
                    badge_icon="🏛️",
                ),
                Mission(
                    title="کاوشگر طبیعت شهری",
                    description="از یک مکان طبیعی و سرسبز شهری بازدید کنید",
                    event_type="visit_poi",
                    conditions_json=json.dumps({"category": "nature"}),
                    target=1,
                    reward_points=25,
                    badge_name="دوست‌دار طبیعت",
                    badge_icon="🌿",
                ),
                Mission(
                    title="تجربه طعم‌های شهری",
                    description="یک نقطه پرانرژی با استریت‌فود یا کافه را کشف کنید",
                    event_type="visit_poi",
                    conditions_json=json.dumps({"category": "energy"}),
                    target=1,
                    reward_points=30,
                    badge_name="شکم‌گرد شهر",
                    badge_icon="☕",
                ),
            ]
        )


def list_active_missions(db: Session):
    repo = MissionsRepository(db)
    return repo.get_active_missions()


def update_user_missions(db: Session, user_id: int, action_type: str, context: dict = None):
    missions_repo = MissionsRepository(db)
    exploration_repo = ExplorationRepository(db)
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
            user_mission.progress += 1
            should_update = True

        elif action_type == "visit_poi" and context:
            if mission.conditions_json:
                try:
                    conds = json.loads(mission.conditions_json)
                    req_cat = conds.get("category")
                    if req_cat and context.get("category") == req_cat:
                        user_mission.progress += 1
                        should_update = True
                except Exception:
                    pass
            else:
                user_mission.progress += 1
                should_update = True

        if should_update and user_mission.progress >= mission.target:
            user_mission.is_completed = True
            user_mission.completed_at = datetime.utcnow()

            XPEngine.award_xp(
                db,
                user_id,
                "MISSION_COMPLETE",
                entity_id=f"mission_{mission.id}",
                reason=f"تکمیل ماموریت '{mission.title}'",
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

    mission_progress_list = []
    active_missions = missions_repo.get_active_missions()

    user_m_map = {um.mission_id: um for um in user_missions}

    for m in active_missions:
        um = user_m_map.get(m.id)
        prog = um.progress if um else 0
        is_comp = um.is_completed if um else False
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
            }
        )

    return {
        "user_id": user_id,
        "score": score,
        "level_stats": level_stats,
        "badges": [
            {
                "name": b.badge_name,
                "icon": b.badge_icon,
                "unlocked_at": b.unlocked_at.isoformat() if b.unlocked_at else None,
            }
            for b in badges
        ],
        "missions": mission_progress_list,
    }
