#!/usr/bin/env bash

if [[ ! -z "${STATIC_FILES_MIRROR}" ]]; then
    echo "Copying static files to ${STATIC_FILES_MIRROR}"
    rsync -a --delete project/presentation/web/static/ "${STATIC_FILES_MIRROR}"
fi

gunicorn -c gunicorn.conf.py main:app
