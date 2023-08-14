#!/bin/sh
# Copyright (c) 2009-2023 Wolfram Schneider, https://bbbike.org
#
# world.cgi - cgi/shell wrapper for bbbike @ world city

umask 002

# load average check
if [ -e /proc/loadavg ]; then
  loadavg="`awk '{ print $1 }' /proc/loadavg`"
else
  loadavg="`uptime | awk '{ print $NF }'`"
fi

max_loadavg=24

if perl -e 'exit $ARGV[1] > $ARGV[2] ? 0 : 1 ' "$loadavg" $max_loadavg; then
	( echo "load average to high, above $max_loadavg: `cat /proc/loadavg`"
	  ps xuawww
	) 1>&2
	exit 2
fi

name="`basename $0 .cgi`"
dirname=`dirname "$0"`
dirname_original=$dirname

# new directory layout
case "$name" in
	index | index.?? )
		name=`basename $dirname`
		dirname="../../../cgi"
		;;
esac

export LANG="C"
export PATH="/opt/local/bin:/bin:/usr/bin:/usr/local/bin"

# English Version
case $name in
	*.en)
		name=`basename $name .en`
		;;
esac

server=$SERVER_NAME
# map api.bbbike.org to www.bbbike.org, will improve caching for API requests
server=$(echo $server | perl -npe 's,^api,www,')

if [ -z "$server" ]; then
	server=bbbike.org
fi

case $server in
    dev* | localhost ) export BBBIKE_RENICE=1 ;;
esac

cache_dir="/opt/bbbike/cache/${server}/$name"
if [ "$server" = "localhost" ]; then
    cache_dir=/tmp/bbbike-${server}-$(whoami)/$name
fi
mkdir -p $cache_dir

#trap 'rm -rf "$cache_dir"; exit 1' 1 2 3 13 15
#trap 'rm -rf "$cache_dir"' 0

# set CPU time and memory limits
# max. 2min
ulimit -t 150

# max. RAM
ulimit -v 5500000


# export NYTPROF=trace=2:start=init:file=/tmp/nytprof.out
# perl -d:NYTProf $dirname_original/$name.cgi #$dirname/bbbike.cgi
data="data-osm/$name"

# fall back to previous version
if [ ! -d "$dirname_original/../$data" -a -d "$dirname_original/../data-osm.old/$name" ]; then
   data="data-osm.old/$name"
fi

#printenv > /tmp/printenv
time env TMPDIR=$cache_dir DATA_DIR="$data" BBBIKE_DATADIR="$data" \
	$dirname_original/$name.cgi

#EOF
