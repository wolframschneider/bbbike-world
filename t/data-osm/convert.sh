#!/bin/sh
# Copyright (c) 2012-2017 Wolfram Schneider, https://bbbike.org
#
# extract a city for further tests

set -e

LANG=C; export LANG
LC_ALL=C; export LC_ALL
PERL_HASH_SEED=12345; export PERL_HASH_SEED
PERL_PERTURB_KEYS=NO; export PERL_PERTURB_KEYS
lsb_release=$(lsb_release -cs)

dir=$(dirname $0)
: ${city=Cusco}
: ${MD5=`which md5 md5sum false | head -1`}

prefix=$dir/tmp
osm=$prefix/${city}
data_osm=$prefix/${city}-data-osm

rm -rf $osm $data_osm
mkdir -p $osm

( cd $osm; ln -s ../../$city.osm.pbf )
world/bin/pbf2osm --gzip $osm/$city.osm.pbf

POI_DB=poi_tmp; export POI_DB
make -s GIT_ID=none TIME="" DATA_OSM_DIR=$data_osm OSM_DIR=$prefix CITIES="$city" convert

( cd $data_osm/$city; find . ! -name '*.gz' -type f -print0 | xargs -0 $MD5 | sort ) > $osm/checksum.$lsb_release

#EOF
