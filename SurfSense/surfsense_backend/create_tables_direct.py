"""
Direct table creation script bypassing Alembic migrations
This creates all tables using SQLAlchemy Base.metadata.create_all()
"""
import asyncio
from app.db import Base, engine

async def create_all_tables():
    """Create all tables defined in SQLAlchemy models."""
    print("Creating all tables from SQLAlchemy models...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully!")

    # Check what tables were created
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """))
        tables = [row[0] for row in result]
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
