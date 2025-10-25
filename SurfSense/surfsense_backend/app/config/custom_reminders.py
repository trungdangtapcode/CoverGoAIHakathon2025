"""Custom reminder configuration - send reminders to specific users at specific times."""

from celery import Celery
from celery.schedules import crontab

# Example: Custom reminder schedules for specific users
# Add your user IDs and their preferred times here

CUSTOM_USER_REMINDERS = [
    {
        "user_id": "your-user-uuid-here",
        "search_space_id": 1,
        "hour": 8,  # 8 AM
        "minute": 0,
        "num_documents": 50,
        "schedule_name": "user-morning-reminder",
    },
    {
        "user_id": "another-user-uuid",
        "search_space_id": 2,
        "hour": 18,  # 6 PM
        "minute": 30,
        "num_documents": 30,
        "schedule_name": "user-evening-reminder",
    },
    # Add more users as needed
]


def register_custom_user_reminders(celery_app: Celery):
    """
    Register custom reminder schedules for specific users.
    
    Call this function after creating the Celery app to add
    personalized schedules for individual users.
    
    Args:
        celery_app: The Celery application instance
    """
    for config in CUSTOM_USER_REMINDERS:
        celery_app.conf.beat_schedule[config["schedule_name"]] = {
            "task": "send_activity_reminder",
            "schedule": crontab(hour=config["hour"], minute=config["minute"]),
            "args": [
                config["user_id"],
                config["search_space_id"],
                config.get("num_documents", 50),
            ],
            "options": {
                "expires": 3600,
            },
        }
    
    print(f"✅ Registered {len(CUSTOM_USER_REMINDERS)} custom user reminders")


# Example usage in celery_app.py:
# from app.config.custom_reminders import register_custom_user_reminders
# register_custom_user_reminders(celery_app)
