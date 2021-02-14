#!/usr/bin/env bash

until flask db upgrade
do
    echo "Waiting for postgres server to become available..."
    sleep 2
done

gunicorn -c gunicorn.conf.py project:app
