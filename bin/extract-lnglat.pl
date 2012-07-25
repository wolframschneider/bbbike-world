#!/usr/local/bin/perl
# Copyright (c) 2012 Wolfram Schneider, http://bbbike.org
#
# extract-lnglat.pl - split the planet.osm into 360x180 lng,lat data tiles
#
# usage: extract-lng-lat.pl > shell.sh

# Aachen:::de::5.88 50.60 6.58 50.99:294951::

my $heatmap = $ENV{HEATMAP} || "heatmap";

for ( -180 .. 179 ) {
    $a = $_ + 1;

    print
      qq[make -s -f Makefile.osm CITIES_FILE=tmp/cities_${_}.txt],
      qq[ CITIES_DB=$heatmap/cities_${_}.csv],
      qq[ OSM_DIR=$heatmap/osm-lnglat/$_ ],
qq[ OSM_PLANET_PBF=$heatmap/osm-lng/p_${_}_-89_${a}_89/p_${_}_-89_${a}_89.osm.pbf ],
      qq[cities-pbf > $heatmap/tmp/log.extract-lnglat.$_\0];
}

# ( cd tmp/osm-lnglat; find . -name '*.pbf' | xargs du -k |sort -n | perl -npe 's,\S+/p_(.*?).osm.pbf,\1,; s,_, ,g' ) > tmp/heatmap.csv

