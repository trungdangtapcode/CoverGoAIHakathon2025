"""Celery tasks for sending periodic activity reminder emails."""

import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.db import SearchSpace, User
from app.services.activity_reminder_service import ActivityReminderService

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")


def get_async_session_factory():
    """Create a new async engine and session factory for each task execution."""
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False, 
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False), engine


async def send_reminder_for_user(user_id: str, search_space_id: int, num_documents: int = 20):
    """
    Send activity reminder email for a specific user and search space.
    
    Args:
        user_id: User ID to send reminder to
        search_space_id: Search space to analyze
        num_documents: Number of documents to analyze (default: 50)
    """
    async_session_factory, engine = get_async_session_factory()
    
    try:
        async with async_session_factory() as session:
            try:
                # Get user details
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User {user_id} not found")
                    return
                
                if not user.email:
                    logger.error(f"User {user_id} has no email address")
                    return
                
                # Verify search space exists and belongs to user
                result = await session.execute(
                    select(SearchSpace).where(
                        SearchSpace.id == search_space_id,
                        SearchSpace.user_id == user_id
                    )
                )
                search_space = result.scalar_one_or_none()
                
                if not search_space:
                    logger.error(f"Search space {search_space_id} not found for user {user_id}")
                    return
                
                # Create reminder service and send email
                reminder_service = ActivityReminderService(session, user_id, user.email)
                
                success, message, insights = await reminder_service.generate_and_send_reminder(
                    search_space_id=search_space_id,
                    num_documents=num_documents,
                    include_connectors=True,
                    include_files=False,
                )
                
                if success:
                    logger.info(f"Activity reminder sent to user {user_id} ({user.email})")
                else:
                    logger.error(f"Failed to send reminder to user {user_id}: {message}")
                    
            except Exception as e:
                logger.error(f"Error sending reminder for user {user_id}: {e}", exc_info=True)
    finally:
        # Clean up engine
        await engine.dispose()


@celery_app.task(name="send_activity_reminder")
def send_activity_reminder_task(user_id: str, search_space_id: int, num_documents: int = 50):
    """
    Celery task to send activity reminder email.
    
    This is the synchronous wrapper for the async send_reminder_for_user function.
    
    Args:
        user_id: User ID to send reminder to
        search_space_id: Search space to analyze
        num_documents: Number of documents to analyze (default: 50)
    """
    import asyncio
    
    try:
        logger.info(f"Starting activity reminder task for user {user_id}, search_space {search_space_id}")
        
        # Run the async function
        asyncio.run(send_reminder_for_user(user_id, search_space_id, num_documents))
        
        logger.info(f"Completed activity reminder task for user {user_id}")
        return {
            "status": "success",
            "user_id": user_id,
            "search_space_id": search_space_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Activity reminder task failed for user {user_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "user_id": user_id,
            "search_space_id": search_space_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@celery_app.task(name="send_all_activity_reminders")
def send_all_activity_reminders_task():
    """
    Celery Beat task to send activity reminders to all active users.
    
    This task can be scheduled to run periodically (e.g., daily at 8 AM).
    It will send reminders to all users who have at least one search space.
    """
    async def send_all_reminders():
        async_session_factory, engine = get_async_session_factory()
        
        try:
            async with async_session_factory() as session:
                try:
                    # Get all users with their search spaces
                    result = await session.execute(
                        select(User, SearchSpace)
                        .join(SearchSpace, User.id == SearchSpace.user_id)
                        .where(User.email.isnot(None))
                        .distinct(User.id)
                    )
                    
                    user_search_spaces = result.all()
                    
                    logger.info(f"Found {len(user_search_spaces)} users to send reminders to")
                    
                    for user, search_space in user_search_spaces:
                        try:
                            # Send reminder for the first search space of each user
                            reminder_service = ActivityReminderService(session, str(user.id), user.email)
                            
                            success, message, insights = await reminder_service.generate_and_send_reminder(
                                search_space_id=search_space.id,
                                num_documents=50,
                                include_connectors=True,
                                include_files=False,
                            )
                            
                            if success:
                                logger.info(f"Sent reminder to {user.email}")
                            else:
                                logger.error(f"Failed to send reminder to {user.email}: {message}")
                                
                        except Exception as e:
                            logger.error(f"Error sending reminder to user {user.id}: {e}", exc_info=True)
                            continue
                    
                    return {
                        "status": "success",
                        "total_users": len(user_search_spaces),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    logger.error(f"Error in send_all_activity_reminders: {e}", exc_info=True)
                    return {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
        finally:
            # Clean up engine
            await engine.dispose()
    
    try:
        logger.info("Starting send_all_activity_reminders task")
        result = asyncio.run(send_all_reminders())
        logger.info(f"Completed send_all_activity_reminders task: {result}")
        return result
        
    except Exception as e:
        logger.error(f"send_all_activity_reminders task failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
