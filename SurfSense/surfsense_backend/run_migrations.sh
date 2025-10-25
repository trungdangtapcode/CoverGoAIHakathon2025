#!/bin/bash

# Migration script for SurfSense backend
# This runs all Alembic migrations (1-35) to set up the database

set -e  # Exit on error

echo "========================================="
echo "Starting SurfSense Database Migrations"
echo "========================================="

# Navigate to backend directory
cd /Users/longle/CoverGo-AI-Hackathon/SurfSense/surfsense_backend

# # Activate virtual environment
# echo "Activating virtual environment..."
# source .venv/bin/activate

# Set PostgreSQL path
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

# Run migrations
echo "Running alembic upgrade head..."
echo "This will apply all 35 migrations (may take 15-30 minutes for fresh database)"
echo ""

alembic upgrade head

# Check status
echo ""
echo "========================================="
echo "Migration Complete!"
echo "========================================="

# Verify alembic version
echo "Current alembic version:"
psql surfsense -c "SELECT version_num FROM alembic_version;"

# List tables created
echo ""
echo "Tables in database:"
psql surfsense -c "\dt" | head -20

echo ""
echo "Looking for our new tables (study_materials, tasks, notes)..."
psql surfsense -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('study_materials', 'tasks', 'notes');"

echo ""
echo "Migration script completed successfully!"
