"""
Quick seed for demo - Creates a pre-selected set of realistic tasks

Usage:
    python quick_seed_demo.py <search_space_id> <user_id>
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.db import Task, get_async_session


async def quick_seed(search_space_id: int, user_id: str):
    """Create a good demo set of tasks"""

    demo_tasks = [
        # 1 Overdue urgent
        {
            "title": "🔴 Submit Q4 financial report to board",
            "description": "Compile and finalize Q4 financial statements including revenue, expenses, and profit margins. Must be reviewed by CFO before board meeting tomorrow.",
            "priority": "URGENT",
            "due_offset": -1,
        },
        # 2 Urgent today
        {
            "title": "🔴 Respond to client complaint about delayed shipment",
            "description": "Major client (Acme Corp) is upset about 2-week delay in their order. Need to provide explanation, compensation offer, and updated delivery timeline today.",
            "priority": "URGENT",
            "due_offset": 0,
        },
        # 3 High priority
        {
            "title": "🟠 Prepare presentation for Monday's team meeting",
            "description": "Create slides covering project status updates, upcoming milestones, and resource allocation for Q1. Include charts and team feedback summary.",
            "priority": "HIGH",
            "due_offset": 1,
        },
        # 4 High priority
        {
            "title": "🟠 Review and approve vacation requests",
            "description": "Process 8 pending vacation requests from team members. Check coverage plans and approve/deny based on project deadlines and team availability.",
            "priority": "HIGH",
            "due_offset": 2,
        },
        # 5 High priority
        {
            "title": "🟠 Update employee handbook with new policies",
            "description": "Incorporate new remote work policy, updated PTO guidelines, and revised expense reimbursement procedures. Get legal approval before distribution.",
            "priority": "HIGH",
            "due_offset": 3,
        },
        # 6 Medium priority
        {
            "title": "🟡 Schedule interviews for Marketing Manager position",
            "description": "Coordinate with 5 candidates and 3 interviewers to set up interview slots. Send calendar invites and prepare interview questions packet.",
            "priority": "MEDIUM",
            "due_offset": 5,
        },
        # 7 Medium priority
        {
            "title": "🟡 Organize team building event for next month",
            "description": "Research venue options, get quotes from caterers, and create poll for team preferences. Budget: $2000 for 20 people. Consider dietary restrictions.",
            "priority": "MEDIUM",
            "due_offset": 7,
        },
        # 8 Medium priority
        {
            "title": "🟡 Update customer contact database",
            "description": "Clean up duplicate entries, verify email addresses, and update company information for top 50 clients. Export updated list for sales team.",
            "priority": "MEDIUM",
            "due_offset": 10,
        },
        # 9 Low priority
        {
            "title": "🟢 Research new project management software options",
            "description": "Compare 3-4 tools (pricing, features, integrations). Create comparison spreadsheet and schedule demos with vendors for team evaluation.",
            "priority": "LOW",
            "due_offset": 14,
        },
        # 10 Low priority
        {
            "title": "🟢 Archive old project files to cloud storage",
            "description": "Move completed project files from 2022-2023 to archive folder. Organize by year and project name. Update file index spreadsheet.",
            "priority": "LOW",
            "due_offset": 21,
        },
    ]

    async for session in get_async_session():
        try:
            print(f"🎯 Creating {len(demo_tasks)} demo tasks for Work Mode...")
            print()

            for i, task_data in enumerate(demo_tasks, 1):
                due_date = datetime.utcnow() + timedelta(days=task_data["due_offset"])

                task = Task(
                    search_space_id=search_space_id,
                    user_id=user_id,
                    title=task_data["title"],
                    description=task_data["description"],
                    source_type="LINEAR",
                    external_id=f"DEMO-{i:03d}",
                    external_url=f"https://linear.app/surfsense/issue/DEMO-{i:03d}",
                    external_metadata={
                        "issue_number": i,
                        "labels": ["demo", "work-mode"],
                    },
                    status="UNDONE",
                    priority=task_data["priority"],
                    due_date=due_date,
                )

                session.add(task)

                overdue = " ⚠️ OVERDUE" if task_data["due_offset"] < 0 else ""
                due_str = due_date.strftime("%b %d")
                print(f"   [{i:2d}] {task_data['title'][:60]:60s} Due: {due_str}{overdue}")

            await session.commit()

            print()
            print("✅ Demo tasks created successfully!")
            print()
            print("📊 Summary:")
            print(f"   🔴 URGENT:  2 tasks (1 overdue)")
            print(f"   🟠 HIGH:    3 tasks")
            print(f"   🟡 MEDIUM:  3 tasks")
            print(f"   🟢 LOW:     2 tasks")
            print()
            print("🎉 Ready for demo! Open Work Mode to see your tasks.")

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
        break


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python quick_seed_demo.py <search_space_id> <user_id>")
        print()
        print("Example:")
        print("  python quick_seed_demo.py 1 550e8400-e29b-41d4-a716-446655440000")
        sys.exit(1)

    search_space_id = int(sys.argv[1])
    user_id = sys.argv[2]

    print("=" * 80)
    print("🚀 Quick Demo Seeder for Work Mode")
    print("=" * 80)
    print(f"Search Space: {search_space_id}")
    print(f"User ID: {user_id}")
    print("=" * 80)
    print()

    asyncio.run(quick_seed(search_space_id, user_id))
