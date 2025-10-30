#!/bin/bash
set +e  # Don't exit on error for this check

# Create n8n database if it doesn't exist
psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE n8n'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'n8n')\gexec
EOSQL

# Check if creation was successful or database already exists
if [ $? -eq 0 ]; then
    echo "n8n database ready"
else
    echo "n8n database check completed"
fi

