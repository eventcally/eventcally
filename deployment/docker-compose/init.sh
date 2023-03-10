set -e
source .env

mkdir -p ${POSTGRES_DATA_PATH}
mkdir -p ${POSTGRES_BACKUP_PATH}
mkdir -p ${CACHE_PATH}
mkdir -p ${STATIC_PATH}
mkdir -p ${FLUENTD_LOG_PATH}
mkdir -p ${FLUENTD_CUSTOM_CONFIG_PATH}
cp ./fluentd-custom.config ${FLUENTD_CUSTOM_CONFIG_PATH}/fluentd-custom.config