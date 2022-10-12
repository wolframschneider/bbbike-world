#!/bin/sh
# Copyright (c) 2012-2022 Wolfram Schneider, https://bbbike.org
#
# extract-disk-usage - calculate uncompressed image size for Garmin & Osmand
#
# For the size, the image size on the device matters, not the size
# of the generated *.zip file, which is for download only

PATH=/usr/local/bin:/bin:/bin:/usr/bin; export PATH

tempfile=$(mktemp);
trap 'rm -f $tempfile' 0

with_path=""; export with_path

set -e

usage () {
    cat <<EOF >&2
$@

usage: $0 [--du ] file.zip
EOF

   exit 1
}

# du(1) compatible output format
case $1 in
    --path | --du ) shift; with_path=true ;;
esac

file="$1"

test -z "$file" && usage "missing file"
test -f "$file" || usage "file does not exists: '$file'"

case $file in
    *.zip ) ;;
    * ) usage "file is not a zip file: '$file'" ;;
esac

unzip -v $file > $tempfile

perl -e '
    my $counter = 0;
    while(<>) {
        chomp;
        if (m, (planet_|Cusco-|srtm[_\-]).*?/(gmapsupp\.img|bbbike-data/.*|shape/.*|.*\.(map|obf|bin|svg|png|mwm|mbtiles))$, ) {
            if (/^\s*(\d+)/) {
                $counter += $1;
            }
        }
    }
    print int($counter / 1024 + 0.5);
' < $tempfile

if [ -n "$with_path" ]; then
    printf "\t$file"
fi
echo ""

#EOF
