"""Service for sending casual activity reminder emails - focus on what happened."""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.insights import InsightResponse
from app.services.email_service import EmailService
from app.services.insights_service import InsightsService

logger = logging.getLogger(__name__)


class ActivityReminderService:
    """Sends casual reminder emails about what's been happening."""

    def __init__(self, session: AsyncSession, user_id: str, user_email: str):
        self.session = session
        self.user_id = user_id
        self.user_email = user_email
        self.insights_service = InsightsService(session, user_id)
        self.email_service = EmailService()

    async def generate_and_send_reminder(
        self,
        search_space_id: int,
        num_documents: int = 50,
        include_connectors: bool = True,
        include_files: bool = False,
    ) -> tuple[bool, str, InsightResponse | None]:
        """Generate and send casual reminder about recent activity."""
        try:
            logger.info(f"Generating activity summary for user {self.user_id}")
            insights = await self.insights_service.generate_insights_and_plan(
                search_space_id=search_space_id,
                num_documents=num_documents,
                include_connectors=include_connectors,
                include_files=include_files,
            )

            html_content = self._generate_html_email(insights)
            text_content = self._generate_text_email(insights)

            subject = f"Hey! Here's what happened - {datetime.now().strftime('%b %d')}"

            success, message = self.email_service.send_html_email(
                to_email=self.user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

            if success:
                logger.info(f"Reminder email sent to {self.user_email}")
                return True, "Reminder sent!", insights
            else:
                logger.error(f"Failed to send reminder: {message}")
                return False, f"Failed: {message}", insights

        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return False, f"Error: {str(e)}", None

    def _generate_html_email(self, insights: InsightResponse) -> str:
        """Generate casual HTML email - focus on what happened."""
        activity = insights.insights
        plan = insights.plan

        activity_items = []
        for doc_type, count in sorted(
            activity.connector_activity.items(), key=lambda x: x[1], reverse=True
        ):
            type_emoji = self._get_doc_type_emoji(doc_type)
            clean_name = doc_type.replace("_CONNECTOR", "").replace("_", " ").title()
            activity_items.append(
                f'<li style="margin: 8px 0; color: #374151; font-size: 15px;">{type_emoji} <strong style="color: #111827;">{count}</strong> from {clean_name}</li>'
            )

        activity_list = "".join(activity_items[:8])
        topics_text = ", ".join(activity.key_topics[:8]) if activity.key_topics else "Nothing specific"

        planning_section = ""
        if plan and plan.action_items:
            priority_emojis = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            
            # Show all action items (up to 5) with full descriptions
            items_html = ""
            for item in plan.action_items[:5]:
                emoji = priority_emojis.get(item.priority, "⚪")
                # Show full description
                # FULL description shown
                items_html += f"""
                <div style="background: #f9fafb; padding: 10px 14px; margin: 8px 0; border-radius: 6px; border-left: 3px solid #6366f1;">
                    <div style="color: #111827; font-weight: 600; font-size: 14px; margin-bottom: 3px;">
                        {emoji} {item.title}
                    </div>
                    <div style="color: #6b7280; font-size: 13px; line-height: 1.4;">
                        {item.description}
                    </div>
                </div>
                """
            
            planning_section = f"""
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <h2 style="color: #111827; font-size: 16px; font-weight: 600; margin: 0 0 10px 0;">
                    � Quick Ideas
                </h2>
                <p style="color: #9ca3af; font-size: 13px; margin: 0 0 12px 0; font-style: italic;">
                    Based on what's been happening, here are some things you might want to consider:
                </p>
                {items_html}
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity Update</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 28px; border-radius: 12px 12px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">👋 Hey there!</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">{datetime.now().strftime('%A, %B %d')}</p>
        </div>
        <div style="background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
            <div style="margin-bottom: 25px;">
                <h2 style="color: #111827; font-size: 19px; font-weight: 600; margin: 0 0 14px 0;">
                    📬 Here's what's been happening
                </h2>
                <p style="color: #4b5563; line-height: 1.7; margin: 0 0 18px 0; font-size: 15px;">
                    {activity.summary}
                </p>
                <div style="background: #f0f9ff; padding: 18px 22px; border-radius: 10px; margin-bottom: 16px; border-left: 4px solid #3b82f6;">
                    <p style="margin: 0 0 12px 0; color: #1e40af; font-weight: 600; font-size: 15px;">
                        📊 What came in:
                    </p>
                    <ul style="margin: 0; padding-left: 20px; line-height: 1.8;">
                        {activity_list}
                    </ul>
                </div>
                <div style="background: #fef3c7; padding: 14px 18px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <p style="margin: 0; color: #78350f; font-size: 14px;">
                        <strong>🏷️ Main topics:</strong> <span style="color: #92400e;">{topics_text}</span>
                    </p>
                </div>
            </div>
            {planning_section}
        </div>
        <div style="background: #f9fafb; padding: 20px; border-radius: 0 0 12px 12px; text-align: center;">
            <p style="margin: 0; color: #9ca3af; font-size: 13px;">
                Just a friendly reminder about your activity 👍
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _generate_text_email(self, insights: InsightResponse) -> str:
        """Generate casual plain text email."""
        activity = insights.insights
        plan = insights.plan

        activity_lines = []
        for doc_type, count in sorted(
            activity.connector_activity.items(), key=lambda x: x[1], reverse=True
        ):
            type_emoji = self._get_doc_type_emoji(doc_type)
            clean_name = doc_type.replace("_CONNECTOR", "").replace("_", " ").title()
            activity_lines.append(f"  {type_emoji} {count} from {clean_name}")

        activity_text = "\n".join(activity_lines[:8])
        topics_text = ", ".join(activity.key_topics[:8]) if activity.key_topics else "Nothing specific"

        planning_text = ""
        if plan and plan.action_items:
            priority_emojis = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
            
            items_text = ""
            for i, item in enumerate(plan.action_items[:3], 1):  # Changed from 5 to 3
                emoji = priority_emojis.get(item.priority, "⚪")
                # Truncate description
                short_desc = item.description[:120] + "..." if len(item.description) > 120 else item.description
                items_text += f"\n{i}. {emoji} {item.title}\n   {item.description}\n"
            
            planning_text = f"""

───────────────────────────────────────────────────────────

� QUICK IDEAS ({plan.estimated_timeframe})

{items_text}
"""

        text = f"""
👋 HEY THERE!
{datetime.now().strftime('%A, %B %d, %Y')}

═══════════════════════════════════════════════════════════

📬 HERE'S WHAT'S BEEN HAPPENING
───────────────────────────────────────────────────────────

{activity.summary}

📊 What came in:
{activity_text}

🏷️ Main topics: {topics_text}
{planning_text}

═══════════════════════════════════════════════════════════

Just a friendly reminder about your activity 👍
"""
        return text

    def _get_doc_type_emoji(self, doc_type: str) -> str:
        """Get emoji for document type."""
        emoji_map = {
            "SLACK": "💬", "NOTION": "📓", "GITHUB": "💻", "GMAIL": "📧",
            "DISCORD": "🎮", "LINEAR": "📋", "JIRA": "🎯", "CONFLUENCE": "📚",
            "CLICKUP": "✅", "GOOGLE_CALENDAR": "📅", "AIRTABLE": "🗂️",
            "LUMA": "🎫", "SEARXNG": "🔍", "BAIDU_SEARCH": "🔎", "ELASTICSEARCH": "🔎",
        }
        
        for key, emoji in emoji_map.items():
            if key in doc_type.upper():
                return emoji
        return "📄"

    async def preview_email(
        self,
        search_space_id: int,
        num_documents: int = 50,
        include_connectors: bool = True,
        include_files: bool = False,
        format: str = "html",
    ) -> dict:
        """Preview email without sending."""
        insights = await self.insights_service.generate_insights_and_plan(
            search_space_id=search_space_id,
            num_documents=num_documents,
            include_connectors=include_connectors,
            include_files=include_files,
        )

        content = self._generate_html_email(insights) if format == "html" else self._generate_text_email(insights)
        subject = f"Hey! Here's what happened - {datetime.now().strftime('%b %d')}"

        return {
            "format": format,
            "subject": subject,
            "content": content,
            "summary": {
                "documents_analyzed": insights.metadata.get("documents_analyzed", 0),
                "action_items_count": len(insights.plan.action_items) if insights.plan else 0,
                "key_topics_count": len(insights.insights.key_topics),
            },
        }
