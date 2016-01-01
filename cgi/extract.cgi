#!/usr/local/bin/perl -T
# Copyright (c) 2011-2016 Wolfram Schneider, http://bbbike.org
#
# extract.cgi - extracts areas in a batch job
#

# CGI.pm treat all parameters as UTF-8 strings
use CGI qw(-utf8);

use lib qw[../world/lib ../lib];
use Extract::Config;
use Extract::CGI;

use strict;
use warnings;

# group writable file
umask(002);

binmode \*STDOUT, ":utf8";
binmode \*STDERR, ":utf8";
$ENV{PATH} = "/bin:/usr/bin";

our $option = {
    'homepage'        => 'http://download.bbbike.org/osm/extract/',
    'script_homepage' => 'http://extract.bbbike.org',

    'max_extracts'              => 50,
    'default_format'            => 'osm.pbf',
    'city_name_optional'        => 0,
    'city_name_optional_coords' => 1,
    'max_skm'                   => 24_000_000,    # max. area in square km
    'max_size'                  => 768_000,       # max area in KB size

    # max count of gps points for a polygon
    'max_coords' => 256 * 256,

    'enable_polygon'      => 1,
    'email_valid_mxcheck' => 1,
    'email_allow_nobody'  => 1,

    'debug'          => "2",
    'request_method' => "GET",

    'supported_languages' => $Extract::Locale::option->{"supported_languages"},
    'language'            => $Extract::Locale::option->{"language"},

    'pro' => 0,

    'with_google_maps'        => 0,
    'enable_google_analytics' => 1,

    # scheduler with priorities (by IP or user agent)
    'enable_priority' => 1,

    # scheduler limits
    'scheduler' => {
        'user_limit' => 25,
        'ip_limit'   => 50
    },

    # configure order of formats in menu
    'formats_order' => [qw/osm shape garmin android svg mapsme srtm/],
};

##########################################################################
# main
#
my $q     = new CGI;
my $debug = $option->{'debug'};
if ( defined $q->param('debug') ) {
    $debug = int( $q->param('debug') );
}

my $extract_config = Extract::Config->new( 'q' => $q, 'option' => $option );
$extract_config->load_config;
$extract_config->check_extract_pro;

my $extract_cgi = Extract::CGI->new(
    'q'      => $q,
    'option' => $option,
    'debug'  => $debug
);

# second page
if ( $q->param("submit") ) {
    $extract_cgi->check_input;
}

# first page, homee page
else {
    $extract_cgi->homepage;
}

__END__;
