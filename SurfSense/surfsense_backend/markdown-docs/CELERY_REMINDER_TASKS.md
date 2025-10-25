# Periodic Activity Reminder Emails (Celery Beat)

## Overview

Automated Celery Beat task that sends activity reminder emails to users on a scheduled basis.

## Configuration

Set these environment variables in your `.env` file:

```bash
# Enable/disable the reminder emails
REMINDER_EMAIL_ENABLED=true

# Schedule: hour and minute (24-hour format)
REMINDER_EMAIL_HOUR=8        # 8 AM
REMINDER_EMAIL_MINUTE=0      # At the top of the hour

# Examples:
# Morning reminder at 8:00 AM:
REMINDER_EMAIL_HOUR=8
REMINDER_EMAIL_MINUTE=0

# Afternoon reminder at 2:30 PM:
REMINDER_EMAIL_HOUR=14
REMINDER_EMAIL_MINUTE=30

# Evening reminder at 6:00 PM:
REMINDER_EMAIL_HOUR=18
REMINDER_EMAIL_MINUTE=0
```

## How It Works

1. **Celery Beat** runs the scheduled task at the configured time
2. **Task queries database** for all users with search spaces
3. **Sends reminder email** to each user using their first search space
4. **Analyzes 50 documents** from connectors (not files) by default

## Tasks Available

### 1. `send_all_activity_reminders` (Scheduled)

Automatically sends reminders to ALL users at the scheduled time.

**Schedule**: Daily at configured hour/minute (default: 8:00 AM)

**What it does**:
- Finds all users with email addresses
- For each user, sends reminder for their first search space
- Analyzes 50 recent documents from connectors
- Logs success/failure for each user

### 2. `send_activity_reminder` (Manual)

Send reminder to a specific user manually.

**Usage**:
```python
from app.tasks.celery_tasks.reminder_tasks import send_activity_reminder_task

# Send reminder to specific user
send_activity_reminder_task.delay(
    user_id="user-uuid-here",
    search_space_id=1,
    num_documents=50
)
```

**Or via Celery CLI**:
```bash
celery -A app.celery_app call send_activity_reminder \
  --args='["user-uuid", 1, 50]'
```

## Running the Tasks

### Start Celery Worker

```bash
celery -A app.celery_app worker --loglevel=info
```

### Start Celery Beat (Scheduler)

```bash
celery -A app.celery_app beat --loglevel=info
```

### Run Both Together

```bash
celery -A app.celery_app worker --beat --loglevel=info
```

## Monitoring

### Check Beat Schedule

```bash
celery -A app.celery_app inspect scheduled
```

### View Active Tasks

```bash
celery -A app.celery_app inspect active
```

### Check Task History

```bash
celery -A app.celery_app events
```

## Testing

### Test Immediately (Manual Trigger)

```python
from app.tasks.celery_tasks.reminder_tasks import send_all_activity_reminders_task

# Run now (don't wait for schedule)
result = send_all_activity_reminders_task.apply_async()
print(result.get())
```

### Or via Python shell:

```bash
python -c "
from app.tasks.celery_tasks.reminder_tasks import send_all_activity_reminders_task
result = send_all_activity_reminders_task.delay()
print('Task ID:', result.id)
"
```

## Logs

Check Celery logs to see task execution:

```bash
# Worker logs
tail -f celery_worker.log

# Or check stdout if running in terminal
celery -A app.celery_app worker --loglevel=info
```

**Example log output**:
```
[2025-10-26 08:00:00] INFO: Starting send_all_activity_reminders task
[2025-10-26 08:00:01] INFO: Found 10 users to send reminders to
[2025-10-26 08:00:05] INFO: Sent reminder to user@example.com
[2025-10-26 08:00:10] INFO: Completed send_all_activity_reminders task
```

## Customization

### Change Schedule

Edit `.env`:
```bash
# Send at 9:30 AM instead
REMINDER_EMAIL_HOUR=9
REMINDER_EMAIL_MINUTE=30
```

Then restart Celery Beat:
```bash
# Stop current Beat process (Ctrl+C)
# Start again
celery -A app.celery_app beat --loglevel=info
```

### Disable Reminders

```bash
REMINDER_EMAIL_ENABLED=false
```

### Multiple Schedules

To send reminders multiple times per day, edit `app/celery_app.py`:

```python
if REMINDER_EMAIL_ENABLED:
    # Morning reminder
    celery_app.conf.beat_schedule["morning-reminders"] = {
        "task": "send_all_activity_reminders",
        "schedule": crontab(hour=8, minute=0),
    }
    
    # Evening reminder
    celery_app.conf.beat_schedule["evening-reminders"] = {
        "task": "send_all_activity_reminders",
        "schedule": crontab(hour=18, minute=0),
    }
```

## Troubleshooting

### Task not running

1. **Check Beat is running**:
   ```bash
   ps aux | grep "celery.*beat"
   ```

2. **Check schedule is loaded**:
   ```bash
   celery -A app.celery_app inspect scheduled
   ```

3. **Check environment variables**:
   ```bash
   echo $REMINDER_EMAIL_ENABLED
   echo $REMINDER_EMAIL_HOUR
   ```

### Emails not sending

1. **Check SMTP configuration** (in `.env`):
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_SENDER_EMAIL=your-email@gmail.com
   SMTP_SENDER_PASSWORD=your-app-password
   SMTP_USE_TLS=true
   ```

2. **Check logs** for email service errors

3. **Test email service** manually:
   ```python
   from app.services.email_service import EmailService
   service = EmailService()
   service.send_text_email("test@example.com", "Test", "Hello")
   ```

### Users not receiving reminders

1. **Check user has email**:
   ```sql
   SELECT id, email FROM users WHERE email IS NOT NULL;
   ```

2. **Check user has search space**:
   ```sql
   SELECT user_id, id FROM searchspaces WHERE user_id = 'user-uuid';
   ```

3. **Check task logs** for specific user errors

## Performance

- **Task duration**: ~5-15 seconds per user (depends on LLM speed)
- **Concurrent tasks**: Celery worker can handle multiple users in parallel
- **Resource usage**: Light on database, moderate on LLM API calls

## Files

- `app/tasks/celery_tasks/reminder_tasks.py` - Task implementation
- `app/celery_app.py` - Celery configuration with Beat schedule
- `app/services/activity_reminder_service.py` - Email generation logic

---

**Quick Start**:
```bash
# 1. Set environment variables
export REMINDER_EMAIL_ENABLED=true
export REMINDER_EMAIL_HOUR=8
export REMINDER_EMAIL_MINUTE=0

# 2. Start Celery with Beat
celery -A app.celery_app worker --beat --loglevel=info

# 3. Wait for scheduled time or trigger manually
python -c "from app.tasks.celery_tasks.reminder_tasks import send_all_activity_reminders_task; send_all_activity_reminders_task.delay()"
```
