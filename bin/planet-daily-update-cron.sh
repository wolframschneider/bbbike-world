#!/bin/sh
# Copyright (c) Jul 2021-2024 Wolfram Schneider, https://bbbike.org
#
# planet-daily-update-cron - wrapper for planet-daily-update called by a cron job
#

PATH="/usr/local/bin:/bin:/usr/bin"; export PATH
set -e

# load standard BBBike extract config
if [ -f $HOME/.bbbikerc ]; then
    . $HOME/.bbbikerc
fi

# tagname config
if [ -f $HOME/.tagnamerc ]; then
    . $HOME/.tagnamerc
fi

: ${time="time nice -6"}

cd $HOME/projects/bbbike
logfile="tmp/log.planet-daily-update"
if [ -e $logfile ]; then
  gzip -f $logfile
fi

sub_planet="sub-planet-daily"
tagname="build-tagname-db"

# ignore missing tagname repo
if [ ! -e ../tagname ]; then
  tagname=""
fi

if ( $time make planet-daily-update && $time make $sub_planet $tagname ) > $logfile 2>&1; then
  exit 0
else
  echo "planet update failed: $?"
  echo ""
  cat $logfile
  exit 1
fi

#EOF
