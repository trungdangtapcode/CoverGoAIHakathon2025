"""
Interactive task seeder - Choose which tasks to create

Usage:
    python seed_tasks_interactive.py
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db import Task, get_async_session


TASK_CATALOG = [
    {
        "id": 1,
        "title": "Fix critical authentication bug in production",
        "description": "Users are unable to login via OAuth. Investigate and fix ASAP. Error: 'invalid_grant' on token exchange.",
        "priority": "URGENT",
        "source_type": "LINEAR",
        "due_date_offset": 0,
        "category": "Bug Fix",
    },
    {
        "id": 2,
        "title": "Implement user profile settings page",
        "description": "Create a new settings page where users can update their profile information, change password, and manage notification preferences.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 2,
        "category": "Feature",
    },
    {
        "id": 3,
        "title": "Database migration for new features",
        "description": "Create and run migrations for the new tasks, notes, and study_materials tables. Ensure backward compatibility.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 1,
        "category": "Database",
    },
    {
        "id": 4,
        "title": "Add unit tests for task service",
        "description": "Write comprehensive unit tests for the TaskService class covering sync, filter, and complete operations.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 5,
        "category": "Testing",
    },
    {
        "id": 5,
        "title": "Update API documentation",
        "description": "Update the API docs to include the new Work Mode endpoints. Add examples and use cases.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 7,
        "category": "Documentation",
    },
    {
        "id": 6,
        "title": "Refactor legacy code in connector module",
        "description": "Clean up and refactor the old connector code to improve maintainability and reduce technical debt.",
        "priority": "LOW",
        "source_type": "LINEAR",
        "due_date_offset": 14,
        "category": "Refactoring",
    },
    {
        "id": 7,
        "title": "Performance optimization for chat queries",
        "description": "Chat responses are slow (>5s). Profile and optimize database queries and vector search. Target: <2s response time.",
        "priority": "URGENT",
        "source_type": "LINEAR",
        "due_date_offset": 0,
        "category": "Performance",
    },
    {
        "id": 8,
        "title": "Implement export functionality",
        "description": "Add ability to export tasks, notes, and chats to CSV/JSON format for backup and data portability.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 3,
        "category": "Feature",
    },
    {
        "id": 9,
        "title": "Add email notifications for due tasks",
        "description": "Send email reminders to users when tasks are due within 24 hours. Use Celery for scheduling.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 10,
        "category": "Feature",
    },
    {
        "id": 10,
        "title": "Improve error messages in UI",
        "description": "Review all error messages and make them more user-friendly and actionable.",
        "priority": "LOW",
        "source_type": "LINEAR",
        "due_date_offset": 21,
        "category": "UX",
    },
    {
        "id": 11,
        "title": "Integrate with Slack for notifications",
        "description": "Add Slack webhook integration to send task updates and completion notifications to team channels.",
        "priority": "HIGH",
        "source_type": "JIRA",
        "due_date_offset": 4,
        "category": "Integration",
    },
    {
        "id": 12,
        "title": "Create user onboarding tutorial",
        "description": "Build an interactive tutorial to help new users understand Work Mode features and workflows.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 12,
        "category": "UX",
    },
    {
        "id": 13,
        "title": "Fix memory leak in Celery workers",
        "description": "Workers are consuming increasing memory over time. Investigate and fix the leak in background task processing.",
        "priority": "URGENT",
        "source_type": "LINEAR",
        "due_date_offset": -1,
        "category": "Bug Fix",
    },
    {
        "id": 14,
        "title": "Add dark mode support",
        "description": "Implement dark mode theme across all pages. Store user preference in database.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 6,
        "category": "Feature",
    },
    {
        "id": 15,
        "title": "Optimize frontend bundle size",
        "description": "Reduce frontend bundle size by code splitting and lazy loading. Target: <500KB initial load.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 15,
        "category": "Performance",
    },
]


def display_menu():
    """Display the task selection menu"""
    print("\n" + "=" * 100)
    print("📋 Available Tasks")
    print("=" * 100)
    print(f"{'ID':<5} {'Priority':<10} {'Category':<15} {'Title':<50} {'Due':<12}")
    print("-" * 100)

    for task in TASK_CATALOG:
        priority_emoji = {
            "URGENT": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }[task["priority"]]

        due_date = datetime.utcnow() + timedelta(days=task["due_date_offset"])
        due_str = due_date.strftime("%b %d")
        if task["due_date_offset"] < 0:
            due_str += " ⚠️"

        print(
            f"{task['id']:<5} {priority_emoji} {task['priority']:<8} {task['category']:<15} "
            f"{task['title'][:48]:<50} {due_str:<12}"
        )

    print("=" * 100)


def get_user_selection():
    """Get task selection from user"""
    print("\n📝 Selection Options:")
    print("  • Enter task IDs (comma-separated): e.g., 1,3,5,7")
    print("  • Enter 'all' to select all tasks")
    print("  • Enter 'urgent' for URGENT priority tasks only")
    print("  • Enter 'high' for HIGH priority tasks only")
    print("  • Enter 'bugs' for bug fixes only")
    print("  • Enter 'features' for features only")

    selection = input("\n👉 Your selection: ").strip().lower()

    if selection == "all":
        return [t["id"] for t in TASK_CATALOG]
    elif selection == "urgent":
        return [t["id"] for t in TASK_CATALOG if t["priority"] == "URGENT"]
    elif selection == "high":
        return [t["id"] for t in TASK_CATALOG if t["priority"] in ["URGENT", "HIGH"]]
    elif selection == "bugs":
        return [t["id"] for t in TASK_CATALOG if t["category"] == "Bug Fix"]
    elif selection == "features":
        return [t["id"] for t in TASK_CATALOG if t["category"] == "Feature"]
    else:
        # Parse comma-separated IDs
        try:
            return [int(x.strip()) for x in selection.split(",") if x.strip()]
        except ValueError:
            print("❌ Invalid selection. Please enter valid task IDs.")
            return []


async def create_selected_tasks(search_space_id: int, user_id: str, task_ids: list[int]):
    """Create the selected tasks in the database"""

    selected_tasks = [t for t in TASK_CATALOG if t["id"] in task_ids]

    if not selected_tasks:
        print("❌ No tasks selected.")
        return

    async for session in get_async_session():
        try:
            print(f"\n✨ Creating {len(selected_tasks)} tasks...")

            for i, template in enumerate(selected_tasks, 1):
                # Calculate due date
                due_date = None
                if template.get("due_date_offset") is not None:
                    due_date = datetime.utcnow() + timedelta(days=template["due_date_offset"])

                task = Task(
                    search_space_id=search_space_id,
                    user_id=user_id,
                    title=template["title"],
                    description=template["description"],
                    source_type=template["source_type"],
                    external_id=f"TASK-{template['id']:03d}",
                    external_url=f"https://linear.app/surfsense/issue/TASK-{template['id']:03d}",
                    external_metadata={
                        "issue_number": template["id"],
                        "category": template["category"],
                        "labels": [template["category"].lower()],
                    },
                    status="UNDONE",
                    priority=template["priority"],
                    due_date=due_date,
                )

                session.add(task)

                # Print progress
                priority_emoji = {"URGENT": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}[
                    template["priority"]
                ]
                print(f"   [{i:2d}] {priority_emoji} {template['title']}")

            await session.commit()

            print(f"\n✅ Successfully created {len(selected_tasks)} tasks!")

        except Exception as e:
            print(f"❌ Error creating tasks: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            break


def main():
    print("=" * 100)
    print("🎯 Work Mode - Interactive Task Seeder")
    print("=" * 100)

    # Get configuration
    search_space_id = input("\n📊 Enter Search Space ID: ").strip()
    user_id = input("👤 Enter User ID (UUID): ").strip()

    if not search_space_id or not user_id:
        print("❌ Search Space ID and User ID are required.")
        return

    try:
        search_space_id = int(search_space_id)
    except ValueError:
        print("❌ Invalid Search Space ID. Must be a number.")
        return

    # Display menu and get selection
    display_menu()
    task_ids = get_user_selection()

    if not task_ids:
        print("❌ No valid tasks selected.")
        return

    # Confirm
    print(f"\n📋 You selected {len(task_ids)} task(s): {task_ids}")
    confirm = input("❓ Proceed with creation? (y/n): ").strip().lower()

    if confirm != "y":
        print("❌ Cancelled.")
        return

    # Create tasks
    asyncio.run(create_selected_tasks(search_space_id, user_id, task_ids))

    print("\n" + "=" * 100)
    print("🎉 Done! Go to Work Mode to see your tasks.")
    print("=" * 100)


if __name__ == "__main__":
    main()
