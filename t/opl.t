#!/usr/local/bin/perl
# Copyright (c) Sep 2012-2016 Wolfram Schneider, http://bbbike.org

BEGIN {
    system(
        "env",   "PATH=/bin:/usr/bin:/usr/local/bin",
        "which", "osmium_convert"
    );
    if ($?) {
        print "1..0 # skip no osmium_convert found, skip tests\n";
        exit;
    }
}

use FindBin;
use lib ( "$FindBin::RealBin/..", "$FindBin::RealBin/../lib",
    "$FindBin::RealBin", );

use Getopt::Long;
use Data::Dumper qw(Dumper);
use Test::More;
use File::Temp qw(tempfile);
use IO::File;
use Digest::MD5 qw(md5_hex);
use File::stat;

use strict;
use warnings;

plan tests => 13;

my $prefix       = 'world/t/data-osm/tmp';
my $pbf_file     = 'world/t/data-osm/tmp/Cusco.osm.pbf';
my $osm_file_gz  = "$prefix/Cusco.osm.opl.gz";
my $osm_file_bz2 = "$prefix/Cusco.osm.opl.bz2";
my $osm_file_xz  = "$prefix/Cusco.osm.opl.xz";

if ( !-f $pbf_file ) {
    die "Directory '$prefix' does not exits\n" if !-d $prefix;
    system(qw(ln -sf ../Cusco.osm.pbf world/t/data-osm/tmp)) == 0
      or die "symlink failed: $?\n";
}

my $pbf_md5 = "58a25e3bae9321015f2dae553672cdcf";
my $opl_md5 = "3846f1f9e053995ad9e804d0ff84dd2a";

# min size of garmin zip file
my $min_size = 200_000;

sub md5_file {
    my $file = shift;
    my $fh = new IO::File $file, "r";
    die "open file $file: $!\n" if !defined $fh;

    my $data = "";
    while (<$fh>) {
        $data .= $_;
    }

    $fh->close;

    my $md5 = md5_hex($data);
    return $md5;
}

######################################################################

if ( !-f $pbf_file ) {
    system(qw(ln -sf ../Cusco.osm.pbf world/t/data-osm/tmp)) == 0
      or die "symlink failed: $?\n";
}

is( md5_file($pbf_file), $pbf_md5, "md5 checksum matched" );

my $tempfile = File::Temp->new( SUFFIX => ".osm" );

system(qq[world/bin/pbf2osm --opl $pbf_file > $tempfile]);
is( $?,                  0,        "pbf2osm --opl converter" );
is( md5_file($tempfile), $opl_md5, "opl gmd5 checksum matched" );

system(
qq[world/bin/pbf2osm --opl-gzip $pbf_file && gzip -dc $osm_file_gz > $tempfile]
);
is( $?,                  0,        "pbf2osm --opl-gzip converter" );
is( md5_file($tempfile), $opl_md5, "opl gzip md5 checksum matched" );

system(
qq[world/bin/pbf2osm --opl-gz $pbf_file && gzip -dc $osm_file_gz > $tempfile]
);
is( $?,                  0,        "pbf2osm --opl-gz converter" );
is( md5_file($tempfile), $opl_md5, "opl gz md5 checksum matched" );

system(
qq[world/bin/pbf2osm --opl-bzip2 $pbf_file && bzcat $osm_file_bz2 > $tempfile]
);
is( $?,                  0,        "pbf2osm --opl-bzip2 converter" );
is( md5_file($tempfile), $opl_md5, "opl bzip2 md5 checksum matched" );

system(
    qq[world/bin/pbf2osm --opl-bz2 $pbf_file && bzcat $osm_file_bz2 > $tempfile]
);
is( $?,                  0,        "pbf2osm --opl-bz2 converter" );
is( md5_file($tempfile), $opl_md5, "opl bz2 md5 checksum matched" );

system(
    qq[world/bin/pbf2osm --opl-xz $pbf_file && xzcat $osm_file_xz > $tempfile]);
is( $?,                  0,        "pbf2osm --opl-xz converter" );
is( md5_file($tempfile), $opl_md5, "opl xz md5 checksum matched" );

__END__
