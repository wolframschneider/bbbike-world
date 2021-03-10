#!/usr/local/bin/perl
# Copyright (c) Sep 2012-2018 Wolfram Schneider, https://bbbike.org

BEGIN {
    my $display = $ENV{BBBIKE_MAPERITIVE_DISPLAY} || $ENV{DISPLAY} || ":200";
    my $display_number = $display;
    $display_number =~ s,^:,,;

    my $lockfile = "/tmp/.X${display_number}-lock";

    if ( $ENV{BBBIKE_MAPERITIVE_DISABLED} ) {
        print "1..0 # skip, maperitive disabled\n";
        exit;
    }
    if ( !$ENV{BBBIKE_TEST_LONG} ) {
        print
          "1..0 # skip, maperitive disabled due not setting BBBIKE_TEST_LONG\n";
        exit;
    }
    if ( !-e $lockfile ) {
        print "1..0 # skip, DISPLAY=$display xvfb not running?\n";
        exit;
    }

    $ENV{DISPLAY} = $display;
}

use FindBin;
use lib "$FindBin::RealBin/../lib";

use Getopt::Long;
use Data::Dumper qw(Dumper);
use Test::More;
use File::Temp qw(tempfile);
use IO::File;
use Digest::MD5 qw(md5_hex);
use File::stat;
use File::Basename;

use Test::More::UTF8;
use Extract::Test::Archive;

use strict;
use warnings;

chdir("$FindBin::RealBin/../..")
  or die "Cannot find bbbike world root directory\n";

my $type = basename( $0, ".t" );    #"svg";

my @svg_styles = qw/google/;
push @svg_styles, qw/osm/ if !$ENV{BBBIKE_TEST_FAST} || $ENV{BBBIKE_TEST_LONG};
push @svg_styles, qw/hiking urbanight wireframe cadastre/
  if $ENV{BBBIKE_TEST_LONG};

my $pbf_file = 'world/t/data-osm/tmp/Cusco-svg.osm.pbf';

if ( !-f $pbf_file ) {
    system( qw(ln -sf ../Cusco.osm.pbf), $pbf_file ) == 0
      or die "symlink failed: $?\n";
}

my $pbf_md5 = "58a25e3bae9321015f2dae553672cdcf";

# min size of garmin zip file
my $min_size = 100_000;

sub md5_file {
    my $file = shift;
    my $fh = new IO::File $file, "r";
    die "open file $file: $!\n" if !defined $fh;

    my $data;
    while (<$fh>) {
        $data .= $_;
    }

    $fh->close;

    my $md5 = md5_hex($data);
    return $md5;
}

######################################################################
sub convert_format {
    my $lang        = shift;
    my $format      = shift;
    my $format_name = shift;

    my $timeout  = 30;
    my $counter  = 0;
    my $tempfile = File::Temp->new( SUFFIX => ".osm" );
    my $st       = 0;

    my $test = Extract::Test::Archive->new(
        'lang'        => $lang,
        'pbf_file'    => $pbf_file,
        'format'      => $format,
        'format_name' => $format_name
    );
    my $city = $test->init_cusco;

    # known styles
    foreach my $style (@svg_styles) {
        my $out = $test->out($style);
        unlink($out);

        system(
qq[world/bin/bomb --timeout=$timeout --screenshot-file=$pbf_file.png -- world/bin/pbf2osm --$format-$style $pbf_file $city]
        );
        is( $?, 0, "pbf2osm --$format-$style converter" );

        system(qq[unzip -tqq $out]);
        is( $?, 0, "valid zip file" );
        $st = stat($out) or warn "stat $out: $!\n";

        my $size = $st ? $st->size : -1;
        cmp_ok( $size, '>', $min_size, "$out: $size > $min_size" );

        system(qq[world/bin/extract-disk-usage.sh $out > $tempfile]);
        is( $?, 0, "extract disk usage check" );

        my $image_size = `cat $tempfile` * 1024;
        cmp_ok( $image_size, '>', $size, "image size: $image_size > $size" );

        $counter += 5;
        $test->validate;
        unlink( $out, "$out.md5", "$out.sha256" );
    }

    return $counter + $test->counter;
}

sub cleanup {
    unlink $pbf_file;
}

#######################################################
#
is( md5_file($pbf_file), $pbf_md5, "md5 checksum matched" );

my $counter = 0;
my @lang    = ("en");
push @lang, ("de") if !$ENV{BBBIKE_TEST_FAST};
push @lang, ("")   if $ENV{BBBIKE_TEST_LONG};

foreach my $lang (@lang) {
    $counter +=
      &convert_format( $lang, $type, ( $type eq 'svg' ? 'SVG' : 'PNG' ) );
}

&cleanup;
plan tests => 1 + $counter;

__END__
