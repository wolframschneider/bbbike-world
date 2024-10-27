#!/usr/local/bin/perl
# Copyright (c) Nov 2015-2023 Wolfram Schneider, https://bbbike.org
#
# extract-formats.pl - test all extract formats

use FindBin;
use lib "$FindBin::RealBin/../lib";

use Extract::Config;
use CGI qw(escape);
use Getopt::Long;
use URI;
use URI::QueryParam;

use strict;
use warnings;

my $debug      = 1;
my $random     = 1;
my $appid      = "";
my $route      = "";                    # gpx route
my $with_lang  = 1;                     # test with random lang
my $user_agent = "BBBike-Test/1.0.0";
my $help;

my $formats = $Extract::Config::formats;
my $server  = $ENV{'BBBIKE_DEV_SERVER'} || 'https://dev1.bbbike.org';
my $email   = $ENV{'BBBIKE_TEST_EMAIL'} || 'Nobody';

# city of Bernau
my $sw_lng = 13.4592;
my $sw_lat = 52.6216;
my $ne_lng = 13.6763;
my $ne_lat = 52.744;

# list of supported languages
my @lang  = ( "en", "de", "fr", "" );
my @words = (
    "Saarbrücken",
    "Berlin",
    "北京市",
    "Москва",
    "กรุงเทพมหานคร",
    "Łódz",
"北京市 กรุงเทพมหานคร Москва Łódz 北京市"
);

sub message {
    print
qq{# please run now: env BBBIKE_DEV_SERVER="$server" $0 | xargs -P2 -n1 -0 /bin/sh -c >/dev/null\0};
}

sub get_random_element {
    my $list = shift;

    my $i = int( rand( scalar(@$list) ) );

    return @$list[$i];
}

sub generate_urls {
    my $expire = time;

    foreach my $key ( keys %$formats ) {

        # currently disabled formats
        next if $key =~ /^(png)-/;

        my $city = "etest";
        my $lang = "";

        if ($with_lang) {
            $lang = get_random_element( \@lang );

            if ($lang) {

                # put some random words into the city
                $city .= " " . get_random_element( \@words );
            }
        }

        my $uri = URI->new("$server/cgi/extract.cgi");
        $uri->query_form(
            "sw_lng" => $sw_lng,
            "sw_lat" => $sw_lat . ( $random ? int( rand(1_000_000) ) : "" ),
            "ne_lng" => $ne_lng,
            "ne_lat" => $ne_lat . ( $random ? int( rand(1_000_000) ) : "" ),
            "email"  => $email,
            "as"     => "1.933243109431466",
            "pg"     => "0.9964839602712444",
            "coords" => "",
            "oi"     => "1",
            "city"   => $city,
            "submit" => "extract",
            "expire" => $expire,
            "ref"    => "test",
            "format" => $key
        );

        # optional parameters
        $uri->query_param( "lang",  $lang )  if $lang ne "";
        $uri->query_param( "route", $route ) if $route ne "";
        $uri->query_param( "appid", $appid ) if $appid ne "";

        my $url = $uri->as_string;

        print qq{curl --connect-timeout 5 -m 36 -sSf "$url" -A "$user_agent"\0};
    }
}

sub usage () {
    <<EOF;

usage: $0 [options]

--debug=0..2        debug option, default: $debug
--random=0..1       random coordinate, default: $random
--appid=<appid>     with appid, default: $appid
--route=<route>     with route, default: $route
--with-lang=0..1    test with random language, default: $with_lang

EOF
}

######################################################################
# main
#
GetOptions(
    "debug=i"     => \$debug,
    "random=i"    => \$random,
    "appid=s"     => \$appid,
    "route=s"     => \$route,
    "with-lang=i" => \$with_lang,
    "help"        => \$help,
) or die usage;

if ($help) {
    print usage;
    exit 0;
}

&message;
&generate_urls;

1;
