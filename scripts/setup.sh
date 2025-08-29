#!/bin/bash

# Setup script for the log processing system

# Initialize the PostgreSQL database
echo "Initializing the PostgreSQL database..."
psql -U postgres -f ../database/init.sql

# Run database migrations
echo "Running database migrations..."
psql -U postgres -f ../database/migrations/001_create_logs_table.sql

# Additional setup tasks can be added here

echo "Setup completed successfully."