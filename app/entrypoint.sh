#!/bin/sh

set -e

if [ -z "${INITIAL_WAIT_PERIOD}" ]; then
    INITIAL_WAIT_PERIOD='10m'
fi

if [ -z "${RENEWAL_INTERVAL}" ]; then
    RENEWAL_INTERVAL='8d'
fi

# sleep for 10 mins to wait for certbot to run
sleep "${INITIAL_WAIT_PERIOD}"

while true; do
    python ./main.py
    sleep "${RENEWAL_INTERVAL}" || x=$?; if [ -n "${x}" ] && [ "${x}" -ne "143" ]; then exit "${x}"; fi 
done