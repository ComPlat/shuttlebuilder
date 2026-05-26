#!/bin/sh
set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting container..."
echo "Running migrations..."

service nginx start
./manage.py migrate
./manage.py initsuperuser

daphne -b 0.0.0.0 -p 8000 ShuttleBuilder.asgi:application