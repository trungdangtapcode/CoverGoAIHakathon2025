"""Email service for sending emails to users."""

import logging
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        """Initialize email service with configuration from environment."""
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.SMTP_SENDER_EMAIL
        self.sender_password = config.SMTP_SENDER_PASSWORD
        self.sender_name = config.SMTP_SENDER_NAME
        self.use_tls = config.SMTP_USE_TLS

    def _create_connection(self) -> smtplib.SMTP:
        """
        Create and return an SMTP connection.

        Returns:
            smtplib.SMTP: Configured SMTP connection

        Raises:
            smtplib.SMTPException: If connection fails
        """
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(self.sender_email, self.sender_password)
            return server
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            raise

    def send_text_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        reply_to: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Send a plain text email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Plain text email content
            reply_to: Optional reply-to email address

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email

            if reply_to:
                msg["Reply-To"] = reply_to

            msg.set_content(content)

            with self._create_connection() as server:
                server.send_message(msg)

            logger.info(f"Text email sent successfully to {to_email}")
            return True, "Email sent successfully"

        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed. Check credentials."
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def send_html_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Send an HTML email with optional plain text fallback.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Optional plain text fallback content
            reply_to: Optional reply-to email address

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email

            if reply_to:
                msg["Reply-To"] = reply_to

            # Attach plain text version if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)

            # Attach HTML version
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            with self._create_connection() as server:
                server.sendmail(self.sender_email, to_email, msg.as_string())

            logger.info(f"HTML email sent successfully to {to_email}")
            return True, "Email sent successfully"

        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed. Check credentials."
            logger.error(error_msg)
            return False, error_msg
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error occurred: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def send_bulk_emails(
        self,
        recipients: list[str],
        subject: str,
        content: str,
        is_html: bool = False,
    ) -> tuple[int, int, list[str]]:
        """
        Send emails to multiple recipients.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            content: Email content (plain text or HTML)
            is_html: Whether content is HTML

        Returns:
            Tuple of (success_count: int, failure_count: int, failed_emails: list)
        """
        success_count = 0
        failure_count = 0
        failed_emails = []

        try:
            with self._create_connection() as server:
                for recipient in recipients:
                    try:
                        if is_html:
                            msg = MIMEMultipart("alternative")
                            msg["Subject"] = subject
                            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
                            msg["To"] = recipient
                            html_part = MIMEText(content, "html")
                            msg.attach(html_part)
                            server.sendmail(
                                self.sender_email, recipient, msg.as_string()
                            )
                        else:
                            msg = EmailMessage()
                            msg["Subject"] = subject
                            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
                            msg["To"] = recipient
                            msg.set_content(content)
                            server.send_message(msg)

                        success_count += 1
                        logger.info(f"Email sent to {recipient}")

                    except Exception as e:
                        failure_count += 1
                        failed_emails.append(recipient)
                        logger.error(f"Failed to send email to {recipient}: {e}")

        except Exception as e:
            logger.error(f"Failed to establish SMTP connection for bulk send: {e}")
            return 0, len(recipients), recipients

        logger.info(
            f"Bulk email complete. Success: {success_count}, Failed: {failure_count}"
        )
        return success_count, failure_count, failed_emails


def get_email_service() -> EmailService:
    """
    Get an instance of the email service.

    Returns:
        EmailService: Configured email service instance
    """
    return EmailService()
