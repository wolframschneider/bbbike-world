#!/bin/sh
# Copyright (c) Aug 2015-2024 Wolfram Schneider, https://bbbike.org
#
# check if git checkout bootstrapping is working

set -e
trap 'rm -rf $dir' 0
dir=$(mktemp -d)
cd $dir

curl --connect-timeout 5 -m 360 -sSfL https://github.com/wosch/bbbike-world/raw/world/bin/bbbike-bootstrap | /bin/sh

#EOF

