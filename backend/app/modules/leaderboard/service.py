import datetime
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.users.models import User
from app.modules.exploration.models import DiscoveredArea, UserPOIState
from app.modules.gamification.models import XPLog, UserScore


def get_leaderboard_data(
    db: Session,
    leaderboard_type: str = "overall",
    limit: int = 10,
    current_user_id: Optional[int] = None,
):
    safe_limit = max(1, min(limit, 50))
    valid_types = ("overall", "weekly", "poi", "exploration")
    l_type = leaderboard_type.lower() if leaderboard_type and leaderboard_type.lower() in valid_types else "overall"

    entries = []
    current_user_info = None

    if l_type == "overall":
        # 1. Overall XP Leaderboard
        top_users = (
            db.query(User)
            .order_by(User.score.desc(), User.id.asc())
            .limit(safe_limit)
            .all()
        )

        for idx, u in enumerate(top_users, start=1):
            entries.append(
                {
                    "rank": idx,
                    "user_id": u.id,
                    "display_name": u.username or f"کاشف #{u.id}",
                    "score": int(u.score or 0),
                }
            )

        if current_user_id:
            c_user = db.query(User).filter(User.id == current_user_id).first()
            if c_user:
                c_score = int(c_user.score or 0)
                higher_count = (
                    db.query(func.count(User.id))
                    .filter(
                        (User.score > c_score)
                        | ((User.score == c_score) & (User.id < current_user_id))
                    )
                    .scalar()
                )
                current_user_info = {
                    "rank": higher_count + 1,
                    "score": c_score,
                    "user_id": current_user_id,
                }

    elif l_type == "weekly":
        # 2. Weekly XP Leaderboard
        now = datetime.datetime.utcnow()
        week_start = (now - datetime.timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        weekly_sub = (
            db.query(
                XPLog.user_id.label("user_id"),
                func.sum(XPLog.xp_value).label("score"),
            )
            .filter(XPLog.timestamp >= week_start)
            .group_by(XPLog.user_id)
            .subquery()
        )

        top_rows = (
            db.query(
                User.id,
                User.username,
                func.coalesce(weekly_sub.c.score, 0),
            )
            .join(weekly_sub, User.id == weekly_sub.c.user_id)
            .order_by(weekly_sub.c.score.desc(), User.id.asc())
            .limit(safe_limit)
            .all()
        )

        for idx, row in enumerate(top_rows, start=1):
            entries.append(
                {
                    "rank": idx,
                    "user_id": row[0],
                    "display_name": row[1] or f"کاشف #{row[0]}",
                    "score": int(row[2] or 0),
                }
            )

        if current_user_id:
            c_score = (
                db.query(func.coalesce(func.sum(XPLog.xp_value), 0))
                .filter(XPLog.user_id == current_user_id, XPLog.timestamp >= week_start)
                .scalar()
            )
            c_score = int(c_score or 0)
            if c_score > 0:
                higher_count = (
                    db.query(func.count(weekly_sub.c.user_id))
                    .filter(
                        (weekly_sub.c.score > c_score)
                        | (
                            (weekly_sub.c.score == c_score)
                            & (weekly_sub.c.user_id < current_user_id)
                        )
                    )
                    .scalar()
                )
                current_user_info = {
                    "rank": (higher_count or 0) + 1,
                    "score": c_score,
                    "user_id": current_user_id,
                }
            else:
                total_weekly_users = db.query(func.count(weekly_sub.c.user_id)).scalar() or 0
                current_user_info = {
                    "rank": total_weekly_users + 1,
                    "score": 0,
                    "user_id": current_user_id,
                }

    elif l_type == "poi":
        # 3. POI Masters Leaderboard
        poi_sub = (
            db.query(
                UserPOIState.user_id.label("user_id"),
                func.count(UserPOIState.id).label("score"),
            )
            .filter(UserPOIState.state == "discovered")
            .group_by(UserPOIState.user_id)
            .subquery()
        )

        top_rows = (
            db.query(
                User.id,
                User.username,
                func.coalesce(poi_sub.c.score, 0),
            )
            .join(poi_sub, User.id == poi_sub.c.user_id)
            .order_by(poi_sub.c.score.desc(), User.id.asc())
            .limit(safe_limit)
            .all()
        )

        for idx, row in enumerate(top_rows, start=1):
            entries.append(
                {
                    "rank": idx,
                    "user_id": row[0],
                    "display_name": row[1] or f"کاشف #{row[0]}",
                    "score": int(row[2] or 0),
                }
            )

        if current_user_id:
            c_score = (
                db.query(func.count(UserPOIState.id))
                .filter(
                    UserPOIState.user_id == current_user_id,
                    UserPOIState.state == "discovered",
                )
                .scalar()
                or 0
            )
            c_score = int(c_score)
            higher_count = (
                db.query(func.count(poi_sub.c.user_id))
                .filter(
                    (poi_sub.c.score > c_score)
                    | (
                        (poi_sub.c.score == c_score)
                        & (poi_sub.c.user_id < current_user_id)
                    )
                )
                .scalar()
            )
            current_user_info = {
                "rank": (higher_count or 0) + 1,
                "score": c_score,
                "user_id": current_user_id,
            }

    elif l_type == "exploration":
        # 4. City Explorers Leaderboard
        exp_sub = (
            db.query(
                DiscoveredArea.user_id.label("user_id"),
                func.count(DiscoveredArea.id).label("score"),
            )
            .group_by(DiscoveredArea.user_id)
            .subquery()
        )

        top_rows = (
            db.query(
                User.id,
                User.username,
                func.coalesce(exp_sub.c.score, 0),
            )
            .join(exp_sub, User.id == exp_sub.c.user_id)
            .order_by(exp_sub.c.score.desc(), User.id.asc())
            .limit(safe_limit)
            .all()
        )

        for idx, row in enumerate(top_rows, start=1):
            entries.append(
                {
                    "rank": idx,
                    "user_id": row[0],
                    "display_name": row[1] or f"کاشف #{row[0]}",
                    "score": int(row[2] or 0),
                }
            )

        if current_user_id:
            c_score = (
                db.query(func.count(DiscoveredArea.id))
                .filter(DiscoveredArea.user_id == current_user_id)
                .scalar()
                or 0
            )
            c_score = int(c_score)
            higher_count = (
                db.query(func.count(exp_sub.c.user_id))
                .filter(
                    (exp_sub.c.score > c_score)
                    | (
                        (exp_sub.c.score == c_score)
                        & (exp_sub.c.user_id < current_user_id)
                    )
                )
                .scalar()
            )
            current_user_info = {
                "rank": (higher_count or 0) + 1,
                "score": c_score,
                "user_id": current_user_id,
            }

    return {
        "type": l_type,
        "entries": entries,
        "current_user": current_user_info,
    }
