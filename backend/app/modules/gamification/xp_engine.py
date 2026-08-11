import math
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.core.config.xp_config import XP_REWARDS, XP_FEEDBACK_TEXTS, XP_BASE_PER_LEVEL
from app.modules.gamification.models import UserScore, XPLog
from app.modules.users.models import User


class XPEngine:
    @staticmethod
    def calculate_progression(total_xp: int) -> Dict[str, Any]:
        """
        Calculates progression statistics based on total XP.
        Formula: level = floor(sqrt(total_xp / 50)) + 1
        """
        clean_score = max(0, total_xp)
        level = math.floor(math.sqrt(clean_score / XP_BASE_PER_LEVEL)) + 1

        xp_current_level_base = int(((level - 1) ** 2) * XP_BASE_PER_LEVEL)
        xp_next_level_base = int((level ** 2) * XP_BASE_PER_LEVEL)

        xp_in_level = clean_score - xp_current_level_base
        xp_needed_for_next = xp_next_level_base - xp_current_level_base
        progress_pct = round(min(100.0, (xp_in_level / max(1, xp_needed_for_next)) * 100.0), 1)

        return {
            "level": level,
            "total_xp": clean_score,
            "xp_in_level": xp_in_level,
            "xp_needed_for_next": xp_needed_for_next,
            "progress_pct": progress_pct,
            "next_level_unlocks": f"Level {level + 1} Rewards & Badges",
        }

    @staticmethod
    def get_user_xp(db: Session, user_id: int) -> int:
        """
        Canonical accessor for user XP score.
        Ensures consistency between user.score and user_score.total_points.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.score is not None:
            return user.score
        user_score = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        return user_score.total_points if user_score else 0

    @staticmethod
    def is_duplicate_event(db: Session, user_id: int, event_type: str, entity_id: str) -> bool:
        """
        Anti-farming check: Returns True if the user has already received XP for this (event_type, entity_id).
        """
        if not entity_id:
            return False

        existing = (
            db.query(XPLog)
            .filter(
                XPLog.user_id == user_id,
                XPLog.event_type == event_type,
                XPLog.entity_id == entity_id,
            )
            .first()
        )
        return existing is not None

    @classmethod
    def award_xp(
        cls,
        db: Session,
        user_id: int,
        event_type: str,
        entity_id: Optional[str] = None,
        reason: Optional[str] = None,
        custom_xp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Core XP Reward Method.
        Checks user tracking preference, anti-farming duplicate rules, awards XP,
        updates User and UserScore tables synchronously, logs the event, and computes feedback.
        """
        # Fetch user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, username=f"explorer_{user_id}", score=0)
            db.add(user)
            db.flush()

        # Check Exploration Tracking Setting
        if getattr(user, "exploration_tracking_enabled", True) is False:
            progression = cls.calculate_progression(user.score or 0)
            return {
                "xp_earned": 0,
                "status": "paused",
                "message": "ردیابی کاوش غیرفعال است (Exploration Tracking Paused).",
                "is_duplicate": False,
                "progression": progression,
                "feedback": {
                    "badge": "+0 XP",
                    "reason": "ردیابی غیرفعال",
                    "level_up": False,
                },
            }

        # Check Anti-Farming Duplicate Rules
        if entity_id and cls.is_duplicate_event(db, user_id, event_type, entity_id):
            progression = cls.calculate_progression(user.score or 0)
            return {
                "xp_earned": 0,
                "status": "duplicate",
                "message": "این فعالیت قبلاً امتیاز داشته است (Duplicate Event).",
                "is_duplicate": True,
                "progression": progression,
                "feedback": {
                    "badge": "+0 XP",
                    "reason": "فعالیت تکراری",
                    "level_up": False,
                },
            }

        # Determine XP value
        xp_amount = custom_xp if custom_xp is not None else XP_REWARDS.get(event_type, 10)
        default_reason = XP_FEEDBACK_TEXTS.get(event_type, "امتیاز جدید کسب شد")
        final_reason = reason or default_reason

        # Calculate levels before and after
        old_score = user.score or 0
        old_level = cls.calculate_progression(old_score)["level"]

        new_score = old_score + xp_amount
        new_progression = cls.calculate_progression(new_score)
        new_level = new_progression["level"]
        level_up = new_level > old_level

        # Synchronize User.score
        user.score = new_score

        # Synchronize UserScore table
        user_score = db.query(UserScore).filter(UserScore.user_id == user_id).first()
        if not user_score:
            user_score = UserScore(user_id=user_id, total_points=new_score, areas_discovered=1)
            db.add(user_score)
        else:
            user_score.total_points = new_score

        # Create XPLog entry for audit trail and anti-farming
        xp_log = XPLog(
            user_id=user_id,
            event_type=event_type,
            xp_value=xp_amount,
            reason=final_reason,
            entity_id=entity_id,
            timestamp=datetime.datetime.utcnow(),
        )
        db.add(xp_log)

        db.commit()
        db.refresh(user)

        return {
            "xp_earned": xp_amount,
            "status": "success",
            "message": f"+{xp_amount} XP ({final_reason})",
            "is_duplicate": False,
            "progression": new_progression,
            "feedback": {
                "badge": f"+{xp_amount} XP",
                "reason": final_reason,
                "level_up": level_up,
                "new_level": new_level if level_up else None,
            },
        }
