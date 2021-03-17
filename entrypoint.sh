#!/usr/bin/env bash

if [[ ! -z "${STATIC_FILES_MIRROR}" ]]; then
    echo "Copying static files to ${STATIC_FILES_MIRROR}"
    rsync -a --delete project/static/ "${STATIC_FILES_MIRROR}"
fi

until flask db upgrade
do
    echo "Waiting for postgres server to become available..."
    sleep 2
done

gunicorn -c gunicorn.conf.py project:app
