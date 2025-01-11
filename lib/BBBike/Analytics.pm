#!/usr/local/bin/perl
#
# Copyright (C) 2008-2018 Wolfram Schneider. All rights reserved.
#
# BBBikeAnalytics - analytics code

package BBBike::Analytics;

use strict;
use warnings;

our %option = ( 'tracker_id' => "" );

sub new {
    my $class = shift;
    my %args  = @_;

    my $self = { %option, %args };

    bless $self, $class;

    return $self;
}

sub google_analytics {
    my $self  = shift;
    my $devel = shift // 0;

    my $q = $self->{'q'};

    my $url = $q->url( -base => 1 );

    if ( !$devel && $url !~ m,^https?://(www|extract|download|garmin)[1-9]?\., )
    {
        return "";    # devel installation
    }

    my $tracker_id = $self->{'tracker_id'};

    return <<EOF;
EOF
}

1;
