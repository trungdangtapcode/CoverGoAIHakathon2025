"""
Delete demo tasks - Removes all tasks with source_type='LINEAR' and external_id starting with 'DEMO-'

Usage:
    python delete_demo_tasks.py <search_space_id> <user_id>
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import and_, delete, select
from app.db import Task, get_async_session


async def delete_demo_tasks(search_space_id: int, user_id: str):
    """Delete all demo tasks for a specific user and search space"""

    async for session in get_async_session():
        try:
            print("=" * 80)
            print("🗑️  Demo Task Deletion Tool")
            print("=" * 80)
            print(f"Search Space: {search_space_id}")
            print(f"User ID: {user_id}")
            print("=" * 80)
            print()

            # First, count how many demo tasks exist
            count_stmt = select(Task).where(
                and_(
                    Task.search_space_id == search_space_id,
                    Task.user_id == user_id,
                    Task.source_type == "LINEAR",
                    Task.external_id.like("DEMO-%")
                )
            )
            result = await session.execute(count_stmt)
            tasks_to_delete = result.scalars().all()
            
            if not tasks_to_delete:
                print("✅ No demo tasks found. Nothing to delete.")
                print()
                return

            print(f"Found {len(tasks_to_delete)} demo task(s) to delete:")
            print()
            
            for i, task in enumerate(tasks_to_delete, 1):
                status_icon = "✓" if task.status == "DONE" else "○"
                print(f"   [{i:2d}] {status_icon} {task.title[:70]}")
            
            print()
            print("⚠️  WARNING: This action cannot be undone!")
            print()
            
            # Ask for confirmation
            confirmation = input("Type 'DELETE' to confirm deletion: ")
            
            if confirmation != "DELETE":
                print()
                print("❌ Deletion cancelled. No tasks were deleted.")
                print()
                return
            
            # Delete the tasks
            delete_stmt = delete(Task).where(
                and_(
                    Task.search_space_id == search_space_id,
                    Task.user_id == user_id,
                    Task.source_type == "LINEAR",
                    Task.external_id.like("DEMO-%")
                )
            )
            
            await session.execute(delete_stmt)
            await session.commit()
            
            print()
            print(f"✅ Successfully deleted {len(tasks_to_delete)} demo task(s)!")
            print()
            print("📊 Summary:")
            print(f"   🗑️  Deleted: {len(tasks_to_delete)} tasks")
            print(f"   📦 Search Space: {search_space_id}")
            print()

        except Exception as e:
            print()
            print(f"❌ Error: {e}")
            print()
            await session.rollback()
            raise
        finally:
            await session.close()
            break


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python delete_demo_tasks.py <search_space_id> <user_id>")
        print()
        print("Example:")
        print("  python delete_demo_tasks.py 1 550e8400-e29b-41d4-a716-446655440000")
        print()
        print("This will delete all demo tasks (external_id starting with 'DEMO-')")
        print("from the specified search space and user.")
        sys.exit(1)

    search_space_id = int(sys.argv[1])
    user_id = sys.argv[2]

    asyncio.run(delete_demo_tasks(search_space_id, user_id))

