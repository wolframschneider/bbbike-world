#!/usr/local/bin/perl
# Copyright (c) Feb 2015-2018 Wolfram Schneider, https://bbbike.org

use FindBin;
use lib "$FindBin::RealBin/../lib";

use CGI;
use Test::More;
use BBBike::Analytics;

use strict;
use warnings;

plan tests => 6;
my $debug = 1;

##########################################################################
# standard english

# fake server hostname
$ENV{HTTP_HOST} = "extract.bbbike.org";

my $q         = new CGI;
my $analytics = BBBike::Analytics->new( 'q' => $q )->google_analytics;

diag "analytics code: $analytics\n" if $debug >= 2;

isnt( $analytics, undef, "analytics class is success" );
cmp_ok( length($analytics), ">", -1, "analytics size" );

$analytics = BBBike::Analytics->new( 'q' => $q, 'tracker_id' => "foobar123" )
  ->google_analytics;
diag "analytics code: $analytics\n" if $debug >= 2;

isnt( $analytics, undef, "analytics class is success" );
cmp_ok( length($analytics), ">", -1, "analytics size" );

#like( $analytics, qr/foobar123/, "tracker id check" );

$ENV{HTTP_HOST} = "dev1.bbbike.org";
$analytics = BBBike::Analytics->new( 'q' => $q )->google_analytics;
isnt( $analytics, undef, "analytics class is success" );
is( $analytics, "", "no analytics on devel machines" );

__END__
