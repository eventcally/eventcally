#!/usr/bin/env bash

until flask db upgrade
do
    echo "Waiting for postgres server to become available..."
    sleep 2
done

BIND_PORT=${PORT:-5000}
gunicorn -c gunicorn.conf.py --bind 0.0.0.0:$BIND_PORT project:app
