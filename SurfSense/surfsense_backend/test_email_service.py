#!/usr/bin/env python3
"""
Quick test script for the email service.
Run this to verify your SMTP configuration is working.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_email_service():
    """Test the email service configuration."""
    from app.services.email_service import EmailService

    print("=" * 60)
    print("Email Service Configuration Test")
    print("=" * 60)
    print()

    # Check if SMTP is configured
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    sender_email = os.getenv("SMTP_SENDER_EMAIL")
    sender_password = os.getenv("SMTP_SENDER_PASSWORD")

    print("Configuration:")
    print(f"  SMTP Server: {smtp_server}")
    print(f"  SMTP Port: {smtp_port}")
    print(f"  Sender Email: {sender_email}")
    print(f"  Password Set: {'✅ Yes' if sender_password else '❌ No'}")
    print()

    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        print("❌ ERROR: SMTP configuration is incomplete!")
        print()
        print("Please set the following in your .env file:")
        if not smtp_server:
            print("  - SMTP_SERVER")
        if not smtp_port:
            print("  - SMTP_PORT")
        if not sender_email:
            print("  - SMTP_SENDER_EMAIL")
        if not sender_password:
            print("  - SMTP_SENDER_PASSWORD")
        print()
        print("See .env.example for reference.")
        return

    # Initialize email service
    try:
        email_service = EmailService()
        print("✅ Email service initialized successfully")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize email service: {e}")
        return

    # Ask if user wants to send a test email
    print("Would you like to send a test email? (y/n): ", end="")
    response = input().strip().lower()

    if response == "y":
        print()
        print("Enter recipient email address: ", end="")
        recipient = input().strip()

        if not recipient:
            print("❌ No recipient provided. Exiting.")
            return

        print()
        print(f"Sending test email to {recipient}...")

        try:
            success, message = email_service.send_text_email(
                to_email=recipient,
                subject="SurfSense Email Service Test",
                content="This is a test email from SurfSense backend.\n\n"
                "If you receive this, your email service is configured correctly!",
            )

            if success:
                print(f"✅ {message}")
                print(f"Test email sent to {recipient}")
            else:
                print(f"❌ Failed to send email: {message}")

        except Exception as e:
            print(f"❌ Error sending email: {e}")
    else:
        print("Test skipped.")

    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_email_service())
