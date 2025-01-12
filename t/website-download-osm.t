#!/usr/local/bin/perl
# Copyright (c) Sep 2012-2021 Wolfram Schneider, https://bbbike.org

BEGIN {
    if ( $ENV{BBBIKE_TEST_NO_NETWORK} ) {
        print "1..0 # skip due no network\n";
        exit;
    }
    if ( $ENV{BBBIKE_TEST_FAST} && !$ENV{BBBIKE_TEST_LONG} ) {
        print "1..0 # skip due fast test\n";
        exit;
    }
}

use FindBin;
use lib "$FindBin::RealBin/../lib";

use utf8;
use Test::More;
use BBBike::Test;

use strict;
use warnings;

my $test = BBBike::Test->new();

my @homepages = qw[
  https://download.bbbike.org
  https://download1.bbbike.org
  https://download2.bbbike.org
  https://download3.bbbike.org
];

my $urls = [
    [ "/osm/planet/planet-latest.osm.pbf.md5", 52 ],
    [ "/osm/planet/planet-daily.osm.pbf.md5",  52 ],

    [ "/osm/planet/planet-latest.osm.pbf.timestamp", 20 ],
    [ "/osm/planet/planet-daily.osm.pbf.timestamp",  20 ],

    [ "/osm/planet/planet-latest.osm.pbf", 69_000_000_000 ],

    [ "/bbbike/data-osm/Ottawa.tbz", 32_000 ],
    [ "/favicon.ico",                1_000 ],
    [ "/robots.txt",                 36 ],
    [ "/sitemap.xml.gz",             1_000 ],
    [ "/index.html",                 600 ],

    [ "/osm/planet/srtm/planet-srtm-e40.osm.pbf", 14_000_000 ],

    #[ "/osm/planet/srtm/Hoehendaten_Freizeitkarte_Europe.osm.pbf", 1_400_000 ],
    [ "/osm/planet/srtm/CHECKSUM.txt",       50 ],
    [ "/osm/planet/sub-srtm/europe.osm.pbf", 1_200_000 ],
    [ "/osm/planet/sub-srtm/CHECKSUM.txt",   50 ],

    [ "/osm/index.html",        1_000 ],
    [ "/osm/extract/",          1_000 ],
    [ "/osm/planet/HEADER.txt", 400 ],
];

# no need for latlon SRTM data
#[ "/osm/srtm/e40/latlon/Lat9Lon98Lat10Lon99.osm.pbf", 2_000_000 ],
#[ "/osm/srtm/e40/latlon/CHECKSUM.txt.gz",             1_000_000 ],

# ads only on production system
plan tests => scalar(@homepages) * $test->myget_counter * scalar(@$urls);

########################################################################
# main
#

foreach my $homepage (@homepages) {
    foreach my $u (@$urls) {
        $test->myget_head( $homepage . $u->[0], $u->[1] );
    }
}

__END__
