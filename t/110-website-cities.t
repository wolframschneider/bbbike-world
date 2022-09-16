#!/usr/local/bin/perl
# Copyright (c) Sep 2012-2018 Wolfram Schneider, https://bbbike.org

BEGIN {
    if ( $ENV{BBBIKE_TEST_NO_NETWORK} || $ENV{BBBIKE_TEST_SLOW_NETWORK} ) {
        print "1..0 # skip due slow or no network\n";
        exit;
    }
    if ( $ENV{BBBIKE_TEST_FAST} && !$ENV{BBBIKE_TEST_LONG} ) {
        print "1..0 # skip due fast check\n";
        exit;
    }
}

use FindBin;
use lib "$FindBin::RealBin/../lib";

use utf8;
use Test::More;
use BBBike::Test;
use Extract::Config;

use strict;
use warnings;

my $test                  = BBBike::Test->new();
my $extract_config        = Extract::Config->new()->load_config_nocgi();
my $enable_google_adsense = 0;

my @homepages = "https://www.bbbike.org";

my @cities = map { chomp; $_ } (`$FindBin::RealBin/../bin/bbbike-db --list`);

my @lang = qw/de en/;
if ( $ENV{BBBIKE_TEST_LONG} ) {
    push @lang, qw/es fr ru/;
}

# for each translation, check a translated term
my $msg = {
    "en" => ["Please enter start and destination street name"],
    "de" => ["Start- und Zielstra&szlig;e der Route eingeben"],
    "da" => ["Angiv start-og bestemmelsessted gadenavn"],
    "es" => ["Por favor, introduzca de inicio y destino"],
    "fr" => ["S'il vous plaît entrez vous nom de la rue de destination"],
    "hr" => ["Molimo unesite početak i odredište naziv ulice"],
    "nl" => ["Geef start-en straatnaam van uw bestemming"],
    "pl" => ["Proszę podać start i ulicy przeznaczenia nazwę"],
    "pt" => ["Por favor, indique de partida eo destino nome da rua"],
    "ru" => [
"Пожалуйста, введите начало и назначения название улицы"
    ],
    "zh" =>
      ["请输入起始和没有门牌号码</乙>目的地的街道名称的"]
};

if ( !$ENV{BBBIKE_TEST_SLOW_NETWORK} ) {
    my $counter_text = 0;
    foreach my $l (@lang) {
        $counter_text += scalar( @{ $msg->{$l} } );
    }
    $counter_text *= scalar(@cities);

    my $counter_html = ( $test->myget_counter * 11 ) + 2;
    my $counter_cities =
      scalar(@cities) *
      ( $test->myget_counter * 2 + 26 ) *
      ( scalar(@lang) + 1 );
    my $counter_ads = 0;

    # ads only on production system
    foreach my $homepage (@homepages) {
        $counter_ads +=
          scalar( grep { !$enable_google_adsense || $_ !~ m,^https?://www, }
              $homepage ) * ( scalar(@cities) * ( scalar(@lang) + 1 ) );
    }

    plan tests => scalar(@homepages) *
      ( $counter_html + $counter_cities + $counter_text ) - $counter_ads;
}
else {
    plan 'no_plan';
}

sub cities {
    my $homepage = shift;

    foreach my $city (@cities) {
        foreach my $lang ( "", @lang ) {
            my $url =
              $lang eq "" ? "$homepage/$city/" : "$homepage/$lang/$city/";
            my $data = _cities( $city, $lang, $url );

            # check for correct translations
            if ( $lang ne "" ) {
                foreach my $text ( @{ $msg->{$lang} } ) {
                    like( $data, qr|$text|,
                        "check translations $url -> $text" );
                }
            }
        }
    }
}

sub _cities {
    my $city = shift;
    my $lang = shift;
    my $url  = shift;

    my $homepage = $url;
    $homepage =~ s,(^https?://[^/]+).*,$1,;

    my $res     = $test->myget($url);
    my $content = $res->decoded_content();
    my $data    = $content;

    like( $content, qr|"real_time"|, "complete html" );
    like(
        $content,
qr{Content-Type" content="text/html; charset=utf-8"|content="text/html; charset=utf-8" http-equiv="Content-Type"},
        "charset"
    );
    like( $content, qr|rel="shortcut|, "icon" );
    like(
        $content,
qr{type="application/opensearchdescription\+xml" .*href="/osp/\S+\.xml"|href="/osp/\S+\.xml" .*type="application/opensearchdescription\+xml"},
        "opensearch"
    );
    like(
        $content,
qr{type="application/atom\+xml" .*href="/feed/bbbike-world.xml| href="/feed/bbbike-world.xml" .*type="application/atom\+xml"},
        "rss"
    );
    like( $content, qr|src="/html/bbbike(-js)?.js"|, "bbbike(-js)?.js" );
    like( $content, qr|href="/html/bbbike.css"|,     "bbbike.css" );
    like( $content, qr|<span id="language_switch">|, "language switch" );
    like( $content, qr|href="https://twitter.com/BBBikeWorld"|, "twitter" );
    like( $content, qr|class="mobile_link|, "mobile link" );
    like( $content, qr|#suggest_start\'\).autocomplete|, "autocomplete start" );
    like( $content, qr|#suggest_via\'\).autocomplete|,   "autocomplete via" );
    like( $content, qr|#suggest_ziel\'\).autocomplete|,  "autocomplete ziel" );
    like( $content, qr|"/images/spinning_wheel32.gif"|,  "spinning wheel" );

    # only on production systems
    if ( $enable_google_adsense && $homepage =~ m,^https?://www, ) {
        like( $content, qr|google_ad_client|,
            "url:$url contains google_ad_client" );
    }

    like( $content, qr|<div id="map"></div>|,    "div#map" );
    like( $content, qr|bbbike_maps_init|,        "bbbike_maps_init" );
    like( $content, qr|city = ".+";|,            "city" );
    like( $content, qr|display_current_weather|, "display_current_weather" );
    like( $content, qr|displayCurrentPosition|,  "displayCurrentPosition" );
    like( $content, qr|<div id="footer">|,       "footer" );
    like( $content, qr|id="other_cities"|,       "other cities" );
    like( $content, qr|</html>|,                 "closing </html>" );

    # skip other tests on slow networks (e.g. on mobile phone links)
    return $data if $ENV{BBBIKE_TEST_SLOW_NETWORK};

    $res = $test->myget( "$homepage/osp/$city.xml", 100 );
    $content = $res->decoded_content();

    like(
        $content,
        qr|<InputEncoding>UTF-8</InputEncoding>|,
        "opensearch input encoding utf8"
    );
    like(
        $content,
        qr|template="https?://www.bbbike.org/cgi/api.cgi\?sourceid=|,
        "opensearch template"
    );
    like(
        $content,
        qr|https?://www.bbbike.org/images/srtbike16.gif</Image>|,
        "opensearch icon"
    );

    return $data;
}

sub html {
    my $homepage = shift;

    $test->myget( "$homepage/osp/Zuerich.en.xml", 100 );
    $test->myget( "$homepage/osp/Toronto.de.xml", 100 );
    $test->myget( "$homepage/osp/Moscow.de.xml",  100 );
    $test->myget( "$homepage/osp/Moscow.en.xml",  100 );

    $test->myget( "$homepage/html/bbbike.css", 7_000 );
    $test->myget(
        "$homepage/html/devbridge-jquery-autocomplete-1.1.2/shadow.png",
        1_000 );

    if ( !$ENV{BBBIKE_TEST_SLOW_NETWORK} ) {
        my $res = $test->myget( "$homepage/html/bbbike-js.js", 100_000 );
        my $content = $res->decoded_content;

        like( $content, qr|#BBBikeGooglemap|, "bbbike js" );
        like( $content, qr|downloadUrl|,      "bbbike js" );

        $test->myget( "$homepage/html/streets.css", 2_000 );
        $test->myget( "$homepage/html/luft.css",    3_000 );
        $test->myget(
"$homepage/html/devbridge-jquery-autocomplete-1.1.2/jquery.autocomplete-min.js",
            1_000
        );
        $test->myget( "$homepage/html/jquery/jquery-1.4.2.min.js", 20_000 );
    }
}

########################################################################
# main
#

foreach my $homepage (@homepages) {
    diag "check homepage $homepage";
    &cities($homepage);
    &html($homepage);
}

__END__
