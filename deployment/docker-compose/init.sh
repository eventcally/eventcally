#!/bin/bash
set -e
source .env

mkdir -p ${POSTGRES_BACKUP_PATH}
mkdir -p ${FLUENTD_LOG_PATH}
mkdir -p ${FLUENTD_CUSTOM_CONFIG_PATH}
mkdir -p ${NGINX_CONFIG_PATH}
cp ./fluentd-custom.config ${FLUENTD_CUSTOM_CONFIG_PATH}/fluentd-custom.config
cp ./nginx.conf ${NGINX_CONFIG_PATH}/nginx.conf