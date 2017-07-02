#!/bin/sh

PID=`ps aux | grep uwsgi | grep -v "grep" | awk '{ print $2 }'`

if [ "$PID" != "" ]; then
  kill -9 $PID
fi

cd /home/hogesuke/nicotune/NicoNewVideoViewerApi
source `which virtualenvwrapper.sh`
workon nicotune
uwsgi uwsgi.ini &