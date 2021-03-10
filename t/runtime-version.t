#!/usr/local/bin/perl
# Copyright (c) Aug 2013-2013 Wolfram Schneider, https://bbbike.org
#
# bbbike-org-runtime-version.t - check if we are using the right command versions
#

BEGIN { }
use Test::More;
use Data::Dumper;

use strict;
use warnings;

my $debug = 1;

my $versions = {
    'debian6' => [

        # version commands, regex to match
        [ [qw/pbzip2 --version/],  qr/ BZIP2 v1.1.[1-9] /m ],
        [ [qw/osmconvert --help/], qr/^osmconvert 0\.8\.11$/m ],
        [
            [qw/osmosis -v/],
            qr/^INFO: Osmosis Version (0\.40\.1|0\.43\.1|0\.46)/m
        ],
        [
            [qw/pigz --version/],
            qr/^pigz (2\.1\.6|2\.2\.[4-9]|2\.3\.1|2\.3)|2\.4/
        ],
        [
            [qw/java -version/],
qr/^(openjdk|java) version "11.0.[2-3]|(1\.8\.0_(131|141|144|151|162|171|181|191|212|222|232|242|252|265|272|275|282|03-Ubuntu)|9\.0\.4|10\.0\.[12])"/m
        ],
        [
            [qw/java -version/],
            qr/^(OpenJDK|Java HotSpot\(TM\)) (64-Bit )?Server VM/m
        ],
        [
            [qw/perltidy -v/],
qr/^This is perltidy, (v20090616|v20101217|v20140328|v20120701|v20170521|v20180220)/
        ],
    ]
};

# test on this OS, by default debian6/squeeze
my $os = 'debian6';

my $version = $versions->{$os};
plan tests => scalar(@$version);

######################################################################
#
foreach my $prog (@$version) {
    warn Dumper($prog) if $debug >= 2;

    my ( $command, $regex ) = @$prog;

    my $shell = join( " ", @$command );

    open( my $fh, "$shell 2>&1 |" ) or die qq{open $shell\n};
    my $data = "";
    while (<$fh>) {
        $data .= $_;
    }

    like( $data, $regex, "run '$shell' and match '$regex'" );
}

__END__
