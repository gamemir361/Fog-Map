"""
Central XP Configuration File
All Experience Point (XP) rewards, progression levels, and event types are defined here.
No hardcoded XP values anywhere else in the application.
"""

XP_REWARDS = {
    "DISCOVER_AREA": 10,         # Discovering a completely new area
    "DISCOVER_POI": 25,          # Discovering a new POI
    "VISIT_POI": 15,             # Visiting a POI for the first time
    "COMPLETE_ROUTE": 50,        # Completing a generated walking route
    "MILESTONE_10_AREAS": 50,    # Milestone: 10 discovered areas
    "MILESTONE_50_AREAS": 200,   # Milestone: 50 discovered areas
    "MILESTONE_100_AREAS": 500,  # Milestone: 100 discovered areas
    "MISSION_COMPLETE": 30,      # Mission completion fallback reward
    "ACHIEVEMENT_UNLOCKED": 100, # Achievement unlock fallback reward
}

XP_FEEDBACK_TEXTS = {
    "DISCOVER_AREA": "منطقه جدید کشف شد!",
    "DISCOVER_POI": "مکان جدید کشف شد!",
    "VISIT_POI": "بازدید از مکان شاخص!",
    "COMPLETE_ROUTE": "مسیر با موفقیت به پایان رسید!",
    "MILESTONE_10_AREAS": "مایلستون ۱۰ منطقه کشف‌شده!",
    "MILESTONE_50_AREAS": "مایلستون ۵۰ منطقه کشف‌شده!",
    "MILESTONE_100_AREAS": "مایلستون ۱۰۰ منطقه کشف‌شده!",
    "MISSION_COMPLETE": "ماموریت تکمیل شد!",
    "ACHIEVEMENT_UNLOCKED": "دستاورد جدید آزاد شد!",
}

# Progression Tuning Parameters
XP_BASE_PER_LEVEL = 50.0
