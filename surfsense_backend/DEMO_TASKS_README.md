# Demo Tasks Management

This guide explains how to create and delete demo tasks for testing Work Mode.

## Overview

Demo tasks are realistic office work tasks (not technical/coding tasks) that simulate a typical work environment. They include:
- Financial reports
- Client communications
- Team management
- HR tasks
- Administrative work

## Creating Demo Tasks

### Method 1: Using the UI (Recommended)

1. Navigate to Work Mode in the application
2. Click the **"Sync Linear"** button
3. 10 demo tasks will be created automatically

### Method 2: Using the Command Line

```bash
cd surfsense_backend
python quick_seed_demo.py <search_space_id> <user_id>
```

**Example:**
```bash
python quick_seed_demo.py 1 550e8400-e29b-41d4-a716-446655440000
```

## Deleting Demo Tasks

To clean up demo tasks when you're done testing:

```bash
cd surfsense_backend
python delete_demo_tasks.py <search_space_id> <user_id>
```

**Example:**
```bash
python delete_demo_tasks.py 1 550e8400-e29b-41d4-a716-446655440000
```

The script will:
1. Show you all demo tasks that will be deleted
2. Ask for confirmation (type `DELETE` to confirm)
3. Delete only tasks with `external_id` starting with `DEMO-`
4. Display a summary of deleted tasks

**Safety Features:**
- Requires explicit confirmation before deletion
- Only deletes tasks marked as demo tasks (DEMO-xxx)
- Shows preview of what will be deleted
- Cannot be undone (use with caution)

## Demo Task Details

The system creates 10 tasks with the following distribution:

### Priority Breakdown:
- 🔴 **URGENT**: 2 tasks (1 overdue, 1 due today)
- 🟠 **HIGH**: 3 tasks (due in 1-3 days)
- 🟡 **MEDIUM**: 3 tasks (due in 5-10 days)
- 🟢 **LOW**: 2 tasks (due in 14-21 days)

### Task Examples:
1. Submit Q4 financial report to board (URGENT, overdue)
2. Respond to client complaint (URGENT, today)
3. Prepare presentation for team meeting (HIGH)
4. Review vacation requests (HIGH)
5. Update employee handbook (HIGH)
6. Schedule interviews (MEDIUM)
7. Organize team building event (MEDIUM)
8. Update customer database (MEDIUM)
9. Research project management tools (LOW)
10. Archive old project files (LOW)

## Technical Details

- **Source Type**: LINEAR
- **External ID Pattern**: DEMO-001, DEMO-002, etc.
- **External URL**: https://linear.app/surfsense/issue/DEMO-xxx
- **Status**: All tasks start as UNDONE
- **Due Dates**: Calculated relative to current date

## Troubleshooting

### Tasks not appearing after creation
- Refresh the page
- Check that you're viewing the correct search space
- Verify the status filter (should be set to "UNDONE")

### Cannot delete tasks
- Ensure you're using the correct search_space_id and user_id
- Check that demo tasks exist (script will show "No demo tasks found" if none exist)
- Verify database connection

### Need to recreate tasks
1. Delete existing demo tasks first
2. Then create new ones
3. This prevents duplicate tasks

## Notes

- Demo tasks are safe to delete at any time
- They don't affect real tasks from actual Linear integration
- You can create demo tasks multiple times for testing
- Each creation adds 10 new tasks (doesn't replace existing ones)

