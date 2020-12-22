#!/usr/bin/env bash

until flask db upgrade
do
    echo "Waiting for postgres server to become available..."
    sleep 2
done

gunicorn --bind 0.0.0.0:5000 project:app
