"""
Seed fake tasks into the database for testing Work Mode

Usage:
    python seed_tasks.py --search_space_id 1 --user_id <uuid> --count 10
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Task, get_async_session


TASK_TEMPLATES = [
    {
        "title": "🔴 Fix critical authentication bug in production",
        "description": "Users are unable to login via OAuth. Investigate and fix ASAP. Error: 'invalid_grant' on token exchange.",
        "priority": "URGENT",
        "source_type": "LINEAR",
        "due_date_offset": 0,  # Today
    },
    {
        "title": "🟠 Implement user profile settings page",
        "description": "Create a new settings page where users can update their profile information, change password, and manage notification preferences.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 2,
    },
    {
        "title": "🟠 Database migration for new features",
        "description": "Create and run migrations for the new tasks, notes, and study_materials tables. Ensure backward compatibility.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 1,
    },
    {
        "title": "🟡 Add unit tests for task service",
        "description": "Write comprehensive unit tests for the TaskService class covering sync, filter, and complete operations.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 5,
    },
    {
        "title": "🟡 Update API documentation",
        "description": "Update the API docs to include the new Work Mode endpoints. Add examples and use cases.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 7,
    },
    {
        "title": "🟢 Refactor legacy code in connector module",
        "description": "Clean up and refactor the old connector code to improve maintainability and reduce technical debt.",
        "priority": "LOW",
        "source_type": "LINEAR",
        "due_date_offset": 14,
    },
    {
        "title": "🔴 Performance optimization for chat queries",
        "description": "Chat responses are slow (>5s). Profile and optimize database queries and vector search. Target: <2s response time.",
        "priority": "URGENT",
        "source_type": "LINEAR",
        "due_date_offset": 0,
    },
    {
        "title": "🟠 Implement export functionality",
        "description": "Add ability to export tasks, notes, and chats to CSV/JSON format for backup and data portability.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 3,
    },
    {
        "title": "🟡 Add email notifications for due tasks",
        "description": "Send email reminders to users when tasks are due within 24 hours. Use Celery for scheduling.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 10,
    },
    {
        "title": "🟢 Improve error messages in UI",
        "description": "Review all error messages and make them more user-friendly and actionable.",
        "priority": "LOW",
        "source_type": "LINEAR",
        "due_date_offset": 21,
    },
    {
        "title": "🟠 Integrate with Slack for notifications",
        "description": "Add Slack webhook integration to send task updates and completion notifications to team channels.",
        "priority": "HIGH",
        "source_type": "JIRA",
        "due_date_offset": 4,
    },
    {
        "title": "🟡 Create user onboarding tutorial",
        "description": "Build an interactive tutorial to help new users understand Work Mode features and workflows.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 12,
    },
    {
        "title": "🔴 Fix memory leak in Celery workers",
        "description": "Workers are consuming increasing memory over time. Investigate and fix the leak in background task processing.",
        "priority": "URGENT",
        "source_type": "LINEAR",
        "due_date_offset": -1,  # Overdue!
    },
    {
        "title": "🟠 Add dark mode support",
        "description": "Implement dark mode theme across all pages. Store user preference in database.",
        "priority": "HIGH",
        "source_type": "LINEAR",
        "due_date_offset": 6,
    },
    {
        "title": "🟡 Optimize bundle size",
        "description": "Reduce frontend bundle size by code splitting and lazy loading. Target: <500KB initial load.",
        "priority": "MEDIUM",
        "source_type": "LINEAR",
        "due_date_offset": 15,
    },
]


async def seed_tasks(search_space_id: int, user_id: str, count: int = 10):
    """Seed fake tasks into the database"""

    async for session in get_async_session():
        try:
            # Clear existing tasks for this search space (optional)
            print(f"🗑️  Clearing existing tasks for search_space_id={search_space_id}...")
            stmt = select(Task).where(Task.search_space_id == search_space_id)
            result = await session.execute(stmt)
            existing_tasks = result.scalars().all()

            for task in existing_tasks:
                await session.delete(task)

            await session.commit()
            print(f"   Deleted {len(existing_tasks)} existing tasks")

            # Create new tasks
            print(f"\n✨ Creating {count} new tasks...")
            tasks_to_create = TASK_TEMPLATES[:count]

            for i, template in enumerate(tasks_to_create, 1):
                # Calculate due date
                due_date = None
                if template.get("due_date_offset") is not None:
                    due_date = datetime.utcnow() + timedelta(days=template["due_date_offset"])

                # Determine status (overdue tasks should be UNDONE)
                status = "UNDONE"

                task = Task(
                    search_space_id=search_space_id,
                    user_id=user_id,
                    title=template["title"],
                    description=template["description"],
                    source_type=template["source_type"],
                    external_id=f"TASK-{i:03d}",
                    external_url=f"https://linear.app/surfsense/issue/TASK-{i:03d}",
                    external_metadata={
                        "issue_number": i,
                        "labels": ["backend" if i % 2 == 0 else "frontend"],
                        "assignee": "AI Assistant",
                    },
                    status=status,
                    priority=template["priority"],
                    due_date=due_date,
                )

                session.add(task)

                # Print progress
                overdue_tag = " ⚠️ OVERDUE" if template.get("due_date_offset", 0) < 0 else ""
                due_str = due_date.strftime("%Y-%m-%d") if due_date else "No due date"
                print(f"   [{i:2d}/{count}] {template['priority']:6s} | {template['title'][:50]:50s} | Due: {due_str}{overdue_tag}")

            await session.commit()

            print(f"\n✅ Successfully created {count} tasks!")
            print(f"\n📊 Task Breakdown:")
            print(f"   🔴 URGENT: {sum(1 for t in tasks_to_create if t['priority'] == 'URGENT')}")
            print(f"   🟠 HIGH:   {sum(1 for t in tasks_to_create if t['priority'] == 'HIGH')}")
            print(f"   🟡 MEDIUM: {sum(1 for t in tasks_to_create if t['priority'] == 'MEDIUM')}")
            print(f"   🟢 LOW:    {sum(1 for t in tasks_to_create if t['priority'] == 'LOW')}")

            overdue_count = sum(1 for t in tasks_to_create if t.get("due_date_offset", 0) < 0)
            if overdue_count > 0:
                print(f"\n   ⚠️  {overdue_count} overdue task(s)")

        except Exception as e:
            print(f"❌ Error seeding tasks: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            break


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Seed fake tasks for Work Mode demo")
    parser.add_argument("--search_space_id", type=int, required=True, help="Search space ID")
    parser.add_argument("--user_id", type=str, required=True, help="User UUID")
    parser.add_argument("--count", type=int, default=10, help="Number of tasks to create (max 15)")

    args = parser.parse_args()

    # Validate count
    if args.count > len(TASK_TEMPLATES):
        print(f"⚠️  Warning: Only {len(TASK_TEMPLATES)} task templates available. Creating {len(TASK_TEMPLATES)} tasks.")
        args.count = len(TASK_TEMPLATES)

    print("=" * 80)
    print("🎯 Work Mode - Task Seeder")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Search Space ID: {args.search_space_id}")
    print(f"  User ID:         {args.user_id}")
    print(f"  Tasks to create: {args.count}")
    print()

    # Run the seeder
    asyncio.run(seed_tasks(args.search_space_id, args.user_id, args.count))

    print("\n" + "=" * 80)
    print("🎉 Done! You can now test Work Mode with realistic tasks.")
    print("=" * 80)


if __name__ == "__main__":
    main()
