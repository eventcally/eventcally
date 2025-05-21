#!/usr/bin/env bash

if [[ ! -z "${STATIC_FILES_MIRROR}" ]]; then
    echo "Copying static files to ${STATIC_FILES_MIRROR}"
    rsync -a --delete project/static/ "${STATIC_FILES_MIRROR}"
fi

if [[ ! -z "${REDIS_URL}" ]]; then
    PONG=`redis-cli -u ${REDIS_URL} ping | grep PONG`
    while [ -z "$PONG" ]; do
        sleep 2
        echo "Waiting for redis server to become available..."
        PONG=`redis-cli -u ${REDIS_URL} ping | grep PONG`
    done
fi

if [[ ! -z "${LIMITER_REDIS_URL}" ]]; then
    PONG=`redis-cli -u ${LIMITER_REDIS_URL} ping | grep PONG`
    while [ -z "$PONG" ]; do
        sleep 2
        echo "Waiting for limiter redis server to become available..."
        PONG=`redis-cli -u ${LIMITER_REDIS_URL} ping | grep PONG`
    done
fi

until flask db upgrade
do
    echo "Waiting for postgres server to become available..."
    sleep 2
done

gunicorn -c gunicorn.conf.py project:app
