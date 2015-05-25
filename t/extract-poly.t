#!/usr/local/bin/perl
# Copyright (c) Sep 2012-2015 Wolfram Schneider, http://bbbike.org

use Test::More;
use Data::Dumper;
use CGI;
use JSON;

use lib qw(world/lib);
use Extract::Poly;

use strict;
use warnings;

my $debug = 0;

sub perl2string {
    my $perl = shift;

    return encode_json($perl);
}

# '13.28300' -> '1.328300E+01'
sub coords_science {
    my $coords = shift;
    my @c;

    foreach my $key (@$coords) {
        push @c, [ sprintf( "%E", $key->[0] ), sprintf( "%E", $key->[1] ) ];
    }

    return \@c;
}

my $poly = new Extract::Poly;

diag("is_lat()") if $debug;
is( $poly->is_lat(0),      1, "lat 50" );
is( $poly->is_lat(50),     1, "lat 50" );
is( $poly->is_lat(-50),    1, "lat -50" );
is( $poly->is_lat(90),     1, "lat 90" );
is( $poly->is_lat(-90),    1, "lat -90" );
is( $poly->is_lat(150),    0, "not lat 150" );
is( $poly->is_lat(-150),   0, "not lat -150" );
is( $poly->is_lat(179),    0, "not lat 179" );
is( $poly->is_lat(-179),   0, "not lat -179" );
is( $poly->is_lat(10150),  0, "not lat 10150" );
is( $poly->is_lat(-10150), 0, "not lat -10150" );

diag("is_lng()") if $debug;
is( $poly->is_lng(0),      1, "lng 50" );
is( $poly->is_lng(50),     1, "lng 50" );
is( $poly->is_lng(-50),    1, "lng -50" );
is( $poly->is_lng(150),    1, "not lng 150" );
is( $poly->is_lng(-150),   1, "not lng -150" );
is( $poly->is_lng(179),    1, "not lng 179" );
is( $poly->is_lng(-179),   1, "not lng -179" );
is( $poly->is_lng(180),    1, "not lng 180" );
is( $poly->is_lng(-180),   1, "not lng -180" );
is( $poly->is_lng(181),    0, "not lng 181" );
is( $poly->is_lng(-181),   0, "not lng -181" );
is( $poly->is_lng(10150),  0, "not lng 10150" );
is( $poly->is_lng(-10150), 0, "not lng -10150" );

diag("parse_coords()") if $debug;
my $coords = [
    [ "13.283", "52.441" ],
    [ "13.494", "52.4411" ],
    [ "13.393", "52.55523" ],
    [ "13.494", "52.591" ],
    [ "13.283", "52.59" ],
    [ "13.399", "52.485999" ],
    [ "13.283", "52.441" ],
];
my $coords_science = &coords_science($coords);

# JSON
my @coords = $poly->parse_coords( encode_json($coords) );
is( perl2string($coords), perl2string( \@coords ), "parse coords from json" );

# Poly
my $obj = { "city" => "test", "coords" => \@coords };
my ( $data, $counter ) = $poly->create_poly_data( 'job' => $obj );
@coords = $poly->parse_coords($data);
is(
    perl2string( \@coords ),
    perl2string($coords_science),
    "parse coords from poly"
);

#diag($data);
#diag Dumper(\@coords) if $debug >= 0;

plan tests => 26;

__END__
