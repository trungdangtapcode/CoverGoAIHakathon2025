# Activity Reminder Email 📬# Activity Reminder Email Service



## What is this?## Overview



A **casual email reminder** that tells you what's been happening in your connected apps. That's it. Simple.An automated email notification service that keeps users informed about their recent activity from third-party connectors and provides AI-powered recommendations for what to do next.



**Main focus**: WHAT HAPPENED  **Focus**: Concise reminders, not comprehensive reports. The email is designed to be quickly scannable and actionable.

**Bonus**: Some planning suggestions (if AI thinks of any)

## What It Does

## Email Example

1. **Analyzes Recent Activity**: Reviews documents from connected sources (Slack, Gmail, Notion, GitHub, etc.)

```2. **Summarizes What Happened**: Creates a brief summary of recent activity

👋 Hey there!3. **Recommends Next Actions**: Uses AI to suggest specific, prioritized next steps

Monday, October 264. **Sends Beautiful Emails**: Delivers professionally formatted HTML emails



📬 Here's what's been happening## Email Structure



Analyzed 50 documents from the last 3 days. Retrieved 50 documents from connected sources.### 🔔 What Happened

- Concise summary of recent activity

📊 What came in:- List of top sources (e.g., "20 from Slack, 15 from Notion")

  💬 20 from Slack- Key topics identified

  📓 15 from Notion  

  💻 10 from GitHub### ✅ What To Do Next

  📧 5 from Gmail- 3-7 prioritized action items

- Each with:

🏷️ Main topics: Project, Design, Meeting  - Clear title

  - Description of what to do

────────────────────────────────────  - Rationale (why this action matters)

  - Priority level (HIGH/MEDIUM/LOW)

📝 Some Ideas (Optional)- Suggested timeframe



Based on what's been happening, here are some things ## API Endpoints

you might want to consider:

### 1. Send Activity Reminder Email

🔴 Review design documents

   Go through the 5 design files...**POST** `/api/v1/insights/email/send`



🟡 Follow up on Slack threadsSend an activity reminder email to the user.

   Several conversations need responses...

#### Request Body

Just a friendly reminder about your activity 👍

``````json

{

## API Endpoints  "search_space_id": 1,

  "num_documents": 50,

### Send Reminder  "include_connectors": true,

  "include_files": false,

**POST** `/api/v1/reminder/send`  "recipient_email": "user@example.com"

}

```bash```

curl -X POST "http://localhost:8002/api/v1/reminder/send" \

  -H "Authorization: Bearer YOUR_TOKEN" \**Parameters:**

  -H "Content-Type: application/json" \- `search_space_id` (required): Search space to analyze

  -d '{- `num_documents` (optional): Documents to analyze (default: 50)

    "search_space_id": 1,- `include_connectors` (optional): Include connector documents (default: true)

    "num_documents": 50,- `include_files` (optional): Include user files (default: false)

    "include_connectors": true- `recipient_email` (optional): Custom recipient (defaults to user's email)

  }'

```#### Response



### Preview Email```json

{

**POST** `/api/v1/reminder/preview`  "success": true,

  "message": "Insights email sent successfully",

```bash  "email_sent_to": "user@example.com",

curl -X POST "http://localhost:8002/api/v1/reminder/preview" \  "insights": {

  -H "Authorization: Bearer YOUR_TOKEN" \    "insights": { ... },

  -H "Content-Type: application/json" \    "plan": { ... },

  -d '{    "metadata": { ... }

    "search_space_id": 1,  }

    "num_documents": 30,}

    "format": "html"```

  }'

```### 2. Preview Email Content



## Use Cases**POST** `/api/v1/insights/email/preview`



- **Daily morning catch-up** - What happened yesterdayPreview the email content without sending it.

- **End of day summary** - Before logging off

- **Weekly roundup** - See what you missed#### Request Body

- **Pre-meeting context** - Quick refresh

```json

## Request Parameters{

  "search_space_id": 1,

```json  "num_documents": 50,

{  "include_connectors": true,

  "search_space_id": 1,           // Required  "include_files": false,

  "num_documents": 50,            // 10-200, default 50  "format": "html"

  "include_connectors": true,     // Default true (Slack, Gmail, etc.)}

  "include_files": false,         // Default false (focus on external activity)```

  "recipient_email": "optional@email.com"  // Optional, defaults to your email

}#### Response

```

```json

## How It Works{

  "format": "html",

1. Fetches recent documents from connectors  "subject": "🔔 Activity Reminder - Oct 26",

2. Summarizes what happened (sources, topics, counts)  "content": "<html>...</html>",

3. Optionally adds AI planning suggestions (if LLM configured)  "insights_summary": {

4. Sends casual, easy-to-read email    "documents_analyzed": 50,

    "action_items_count": 5,

## Email Structure    "key_topics_count": 8

  }

### Main Content (Always Included)}

- ✅ Summary of recent activity```

- ✅ List of sources with counts

- ✅ Key topics identified## Use Cases

- ✅ Casual, scannable format

### 1. Daily Morning Reminder

### Bonus Section (Optional)Send a daily email at 8 AM with yesterday's activity:

- 📝 AI-generated suggestions (if LLM available)

- 📝 Priority levels```bash

- 📝 Timeframe recommendationscurl -X POST "http://localhost:8002/api/v1/insights/email/send" \

  -H "Authorization: Bearer TOKEN" \

## Scheduling Examples  -H "Content-Type: application/json" \

  -d '{

### Daily Reminder (8 AM)    "search_space_id": 1,

```cron    "num_documents": 30,

0 8 * * * curl -X POST "http://localhost:8002/api/v1/reminder/send" \    "include_connectors": true,

  -H "Authorization: Bearer $TOKEN" \    "include_files": false

  -H "Content-Type: application/json" \  }'

  -d '{"search_space_id": 1, "num_documents": 30}'```

```

### 2. Weekly Summary

### End of Day (6 PM)Send a weekly recap every Monday:

```cron

0 18 * * * curl -X POST "http://localhost:8002/api/v1/reminder/send" \```bash

  -H "Authorization: Bearer $TOKEN" \curl -X POST "http://localhost:8002/api/v1/insights/email/send" \

  -H "Content-Type: application/json" \  -H "Authorization: Bearer TOKEN" \

  -d '{"search_space_id": 1, "num_documents": 20}'  -H "Content-Type: application/json" \

```  -d '{

    "search_space_id": 1,

## Configuration    "num_documents": 100,

    "include_connectors": true,

### SMTP (Required)    "include_files": false

Already configured via environment variables:  }'

- `SMTP_SERVER````

- `SMTP_PORT`  

- `SMTP_SENDER_EMAIL`### 3. End of Day Check-in

- `SMTP_SENDER_PASSWORD`Send evening reminder with action items for tomorrow:

- `SMTP_USE_TLS`

```bash

### LLM (Optional)curl -X POST "http://localhost:8002/api/v1/insights/email/send" \

Configure in search space settings for planning suggestions.  -H "Authorization: Bearer TOKEN" \

- **Without LLM**: Email still works, no planning section  -H "Content-Type: application/json" \

- **With LLM**: Adds bonus planning ideas  -d '{

    "search_space_id": 1,

## Best Practices    "num_documents": 20,

    "include_connectors": true

✅ **DO:**  }'

- Use 30-50 docs for daily, 80-100 for weekly```

- Focus on connectors (`include_connectors: true`)

- Preview before automating## Email Preview

- Send once or twice a day max

### HTML Email (Desktop/Mobile)

❌ **DON'T:**

- Include files unless needed (focus on external activity)```

- Analyze too many docs (keep under 100)┌─────────────────────────────────────┐

- Send too frequently (not spammy)│   🔔 Activity Reminder              │

│   Monday, October 26, 2025          │

## Python Example├─────────────────────────────────────┤

│                                     │

```python│ 📬 What Happened                    │

import requests│                                     │

│ Analyzed 50 documents from the      │

def send_reminder(token: str, search_space_id: int):│ last 3 days. Retrieved 50          │

    response = requests.post(│ documents from connected sources.   │

        "http://localhost:8002/api/v1/reminder/send",│                                     │

        headers={"Authorization": f"Bearer {token}"},│ 📊 Recent Activity:                 │

        json={│  💬 20 from Slack                   │

            "search_space_id": search_space_id,│  📓 15 from Notion                  │

            "num_documents": 50,│  💻 10 from GitHub                  │

            "include_connectors": True,│  📧 5 from Gmail                    │

            "include_files": False│                                     │

        }│ 🏷️ Key Topics:                      │

    )│  Project, Design, Meeting           │

    │                                     │

    if response.status_code == 200:├─────────────────────────────────────┤

        print("✅ Reminder sent!")│                                     │

    else:│ ✅ What To Do Next                  │

        print(f"❌ Failed: {response.text}")│                                     │

```│ ┌─────────────────────────────┐   │

│ │ 🔴 Review design documents  │   │

## Files│ │                             │   │

│ │ Go through the 5 design     │   │

- `app/services/activity_reminder_service.py` - Email generation│ │ files and consolidate...    │   │

- `app/routes/activity_reminder_routes.py` - API endpoints│ │                             │   │

- `app/app.py` - Registered under `/api/v1/reminder/*`│ │ 💡 Multiple design          │   │

│ │    discussions indicate...  │   │

## Troubleshooting│ └─────────────────────────────┘   │

│                                     │

**Email not sending?**│ ⏱️ Suggested timeframe: 1-2 weeks   │

- Check SMTP configuration│                                     │

- Verify email service with test email└─────────────────────────────────────┘

- Check logs for errors```



**No planning suggestions?**### Plain Text Email (Fallback)

- Configure LLM in search space (optional)

- Email works fine without LLM```

🔔 ACTIVITY REMINDER

**Email looks weird?**Monday, October 26, 2025

- Use preview endpoint first============================================================

- Test in Gmail/Outlook web

- Plain text fallback available📬 WHAT HAPPENED

------------------------------------------------------------

---

Analyzed 50 documents from the last 3 days...

**TL;DR**: Casual email about what happened. Planning is optional bonus. Keep it simple.

📊 Recent Activity:
  💬 20 from Slack
  📓 15 from Notion
  💻 10 from GitHub

🏷️ Key Topics: Project, Design, Meeting

============================================================

✅ WHAT TO DO NEXT
------------------------------------------------------------

Based on your recent activity, here are recommended next steps:

1. 🔴 REVIEW DESIGN DOCUMENTS
   
   Go through the 5 design files and consolidate...
   
   💡 Multiple design discussions indicate this is key focus

⏱️ Suggested timeframe: 1-2 weeks
```

## Configuration

### SMTP Settings

Required environment variables (already configured in SurfSense):
- `SMTP_SERVER`: SMTP server address
- `SMTP_PORT`: SMTP port
- `SMTP_SENDER_EMAIL`: Sender email
- `SMTP_SENDER_PASSWORD`: Email password
- `SMTP_SENDER_NAME`: Display name
- `SMTP_USE_TLS`: Use TLS (true/false)

### LLM Configuration

Users must have a strategic LLM configured in their search space for AI-powered recommendations.

## Best Practices

### ✅ DO

- **Focus on connectors**: Set `include_connectors: true`, `include_files: false`
- **Use moderate document counts**: 30-50 for daily, 80-100 for weekly
- **Schedule regularly**: Set up cron jobs for automated delivery
- **Test with preview**: Use preview endpoint before sending

### ❌ DON'T

- **Don't include files** (unless specifically needed) - focus on external activity
- **Don't analyze too many docs**: Keep it under 100 for faster processing
- **Don't send too frequently**: Once or twice per day maximum
- **Don't ignore email errors**: Check the response for delivery status

## Scheduling (Recommended)

### Using Cron

**Daily morning reminder (8 AM):**
```cron
0 8 * * * curl -X POST "http://localhost:8002/api/v1/insights/email/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_space_id": 1, "num_documents": 30}'
```

**Weekly summary (Monday 9 AM):**
```cron
0 9 * * 1 curl -X POST "http://localhost:8002/api/v1/insights/email/send" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"search_space_id": 1, "num_documents": 100}'
```

### Using Celery (Recommended)

Create a periodic task in `celery_app.py`:

```python
@celery_app.task
def send_daily_reminder(user_id: str, search_space_id: int):
    """Send daily activity reminder."""
    # Your implementation here
    pass

# Schedule in celerybeat
celery_app.conf.beat_schedule = {
    'daily-reminder': {
        'task': 'send_daily_reminder',
        'schedule': crontab(hour=8, minute=0),
        'args': (user_id, search_space_id)
    },
}
```

## Customization

### Email Content

Edit `/app/services/insights_notification_service.py`:

- **Subject line**: Line 61
- **HTML template**: Lines 80-170
- **Text template**: Lines 175-210

### Action Item Priority Colors

In `_generate_html_email()`:

```python
priority_colors = {
    "HIGH": "#ef4444",    # Red - urgent
    "MEDIUM": "#f59e0b",  # Orange - important
    "LOW": "#22c55e",     # Green - can wait
}
```

## Troubleshooting

### Email not sending

**Check SMTP configuration:**
```bash
# Test email service
python -c "from app.services.email_service import EmailService; \
           s = EmailService(); \
           print(s.send_text_email('test@example.com', 'Test', 'Hello'))"
```

**Common issues:**
- Invalid SMTP credentials
- SMTP port blocked by firewall
- TLS/SSL mismatch

### No action items generated

**Possible causes:**
- No LLM configured
- Insufficient documents
- LLM API error

**Solution:**
- Configure strategic LLM in search space settings
- Increase `num_documents`
- Check LLM API keys and quotas

### Email formatting broken

**Check email client:**
- Test with web-based Gmail/Outlook
- Use preview endpoint to verify HTML
- Fallback to text format if needed

## Performance

- **Email generation**: 2-5 seconds
- **LLM analysis**: 5-15 seconds (depends on LLM)
- **Email delivery**: 1-3 seconds
- **Total**: ~10-25 seconds per email

## Integration Example

### Python Client

```python
import requests

def send_activity_reminder(token: str, search_space_id: int):
    """Send activity reminder email."""
    response = requests.post(
        "http://localhost:8002/api/v1/insights/email/send",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "search_space_id": search_space_id,
            "num_documents": 50,
            "include_connectors": True,
            "include_files": False
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Email sent to {data['email_sent_to']}")
        print(f"📊 Analyzed {data['insights']['metadata']['documents_analyzed']} documents")
        print(f"✅ {len(data['insights']['plan']['action_items'])} action items")
    else:
        print(f"❌ Failed: {response.text}")

# Usage
send_activity_reminder("your_token", 1)
```

## Future Enhancements

- [ ] Digest mode (multiple days in one email)
- [ ] Email templates selection
- [ ] Unsubscribe functionality
- [ ] Email frequency preferences
- [ ] Team-wide reminders
- [ ] Slack/Discord integration
- [ ] Mobile push notifications

## Related Services

- **Insights Service** (`insights_routes.py`): Generate insights without email
- **Email Service** (`email_service.py`): Core email sending functionality
- **LLM Service** (`llm_service.py`): AI-powered recommendations

## Support

For issues or questions:
- Check logs: `/var/log/surfsense/`
- Test preview endpoint first
- Verify SMTP configuration
- Ensure LLM is configured

---

**Version**: 1.0  
**Last Updated**: October 26, 2025  
**Dependencies**: insights_service, email_service, LLM service
