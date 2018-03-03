#!/bin/sh

SCRIPT_DIR=$(cd $(dirname $0); pwd)
PID=`ps aux | grep uwsgi | grep -v "grep" | awk '{ print $2 }'`

if [ "$PID" != "" ]; then
  kill -9 $PID
fi

cd $SCRIPT_DIR

uwsgi uwsgi.ini &
